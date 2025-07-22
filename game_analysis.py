from functools import reduce
import itertools
from operator import mul
from anytree import Node, NodeMixin, PreOrderIter
import numpy as np
from math import factorial
import torch

import tqdm

def create_state_action_lists():
    root_states = Node('root_states')

    root_actions = Node('root_actions')

    for picking in [0, 1, 2, 3, 4, 5, 6]:
        pick_node = Node('action_pick_group', parent=root_actions, n_pick=picking)
        for comb in itertools.combinations(range(6), picking):
            specific_pick = Node('action_pick', parent=pick_node, pick_inds=comb)

    forfeit_pick = Node('action_pick', parent=root_actions, pick_inds=None)
    action_list = list(PreOrderIter(root_actions, filter_=lambda n: n.name=='action_pick'))

    triplet_layer = [
        Node('triplet', parent=root_states, triplet=-1),
        Node('triplet', parent=root_states, triplet=1),
        Node('triplet', parent=root_states, triplet=2),
        Node('triplet', parent=root_states, triplet=3),
        Node('triplet', parent=root_states, triplet=4),
        Node('triplet', parent=root_states, triplet=5),
        Node('triplet', parent=root_states, triplet=6),
    ]

    dice_nodes = []
    for parent in triplet_layer:
        if parent.triplet > 0:
            dice_nodes += [
                Node('dice_node', parent=parent, dice_left=3),
                Node('dice_node', parent=parent, dice_left=2),
                Node('dice_node', parent=parent, dice_left=1),
            ]
        else:
            dice_nodes += [
                Node('dice_node', parent=triplet_layer[0], dice_left=6),
                Node('dice_node', parent=triplet_layer[0], dice_left=5),
                Node('dice_node', parent=triplet_layer[0], dice_left=4),
                Node('dice_node', parent=triplet_layer[0], dice_left=3),
                Node('dice_node', parent=triplet_layer[0], dice_left=2),
                Node('dice_node', parent=triplet_layer[0], dice_left=1),
            ]

    for dice_node in dice_nodes:
        dice_left = dice_node.dice_left
        probs = []
        for dice_values in itertools.combinations_with_replacement([1, 2, 3, 4, 5, 6], dice_left):
            _, counts = np.unique(dice_values, return_counts=True)
            denom = reduce(mul, (factorial(c) for c in counts), 1)
            prob = (factorial(dice_left) // denom) / (6**dice_left)

            probs.append(prob)
            Node('leaf', parent=dice_node, data=dice_values, prob=prob)

    state_list = list(PreOrderIter(root_states, filter_=lambda n: n.name=='leaf'))
    return state_list, action_list

state_list, action_list = create_state_action_lists()

def calculate_gain(state, picked_vals, ignore_leftover=False):
    triplet_cont_val = state.parent.parent.triplet
    triplet_cont_gain = 100 * triplet_cont_val if triplet_cont_val != 1 else 1000
    dice_counts = np.bincount(picked_vals, minlength=7)
    new_triplets = [i for i, c in enumerate(dice_counts) if c>=3]
    new_triplet_cont_val = triplet_cont_val

    if picked_vals == (1, 2, 3, 4, 5, 6):
        return 1000, 0, -1

    for twoset_inds in itertools.combinations([1, 2, 3, 4, 5, 6], 3):
        vals = tuple(2 if a in twoset_inds else 0 for a in [1, 2, 3, 4, 5, 6])
        if tuple(dice_counts[1:]) == vals:
            return 500, 0, -1


    gain = 0

    if triplet_cont_val > 0:
        gain += dice_counts[triplet_cont_val] * triplet_cont_gain
        dice_counts[triplet_cont_val] = 0

    for v in new_triplets:
        triplet_gain = 100 * v if v != 1 else 1000
        gain += (dice_counts[v]-2) * triplet_gain
        dice_counts[v] = 0
        new_triplet_cont_val = v

    gain += dice_counts[1] * 100
    gain += dice_counts[5] * 50

    dice_counts[1] = 0
    dice_counts[5] = 0

    if not ignore_leftover and np.sum(dice_counts) > 0:
        raise ValueError('Invalid pick: Unusable dice')

    return gain, state.parent.dice_left - len(picked_vals), new_triplet_cont_val




def calculate_transition(dice_left, triplet_cont_val):
    transition_prob = np.zeros(len(state_list))
    for i, n in enumerate(state_list):
        if n.parent.dice_left!=dice_left or n.parent.parent.triplet != triplet_cont_val:
            transition_prob[i] = 0
        else:
            transition_prob[i] = n.prob
    return np.array(transition_prob)


def compute_transition_data():
    # gain, dice_left, triplet_cont, episode_end, valid
    pseudo_state_action_table = np.zeros((len(state_list), len(action_list), 5), dtype=int)
    pseudo_transition_table = np.zeros((len(state_list), len(action_list), len(state_list)))

    for i_state, state in enumerate(state_list):
        dice_left = state.parent.dice_left

        for i_action, action in enumerate(action_list):
            pick_inds = action.pick_inds
            if pick_inds is None:
                # Forfeiting episode
                pseudo_state_action_table[i_state, i_action] = (-1, 0, 0, 1, 1)
            elif len(pick_inds) == 0:
                # Test if any choices are possible:
                move_possible = False
                for picking in range(1, dice_left+1):
                    for comb in itertools.combinations(range(dice_left), picking):
                        picked_vals = tuple(state.data[i] for i in comb)
                        try:
                            calculate_gain(state, picked_vals)
                            move_possible = True
                        except ValueError:
                            pass

                if move_possible:
                    # Ending episode with cash-in
                    gain, _, _ = calculate_gain(state, state.data, ignore_leftover=True)
                    pseudo_state_action_table[i_state, i_action] = (gain, -1, -1, 1, 1)
                else:
                    pseudo_state_action_table[i_state, i_action] = (-1, 0, 0, 1, 0)

            elif np.max(pick_inds) >= state.parent.dice_left:
                pseudo_state_action_table[i_state, i_action] = (-1, 0, 0, 1, 0)
            else:

                picked_vals = tuple(state.data[i] for i in pick_inds)

                try:
                    gain, next_dice_left, next_triplet = calculate_gain(state, picked_vals)
                    if next_dice_left == 0:
                        next_dice_left = 6
                        next_triplet = -1

                    pseudo_state_action_table[i_state, i_action] = (gain, next_dice_left, i_action, 0, 1)
                    pseudo_transition_table[i_state, i_action] = calculate_transition(next_dice_left, next_triplet)
                except ValueError:
                    pseudo_state_action_table[i_state, i_action] = (-1, 0, 0, 1, 0)

    return pseudo_state_action_table, pseudo_transition_table

def gather(arr, idx_start, n_slice):
    # arr has shape (n_vals,)
    # idx_start has shape (n_actions,)
    # out should have shape (n_actions, n_slice)
    gather_inds = idx_start.reshape(-1, 1) + np.arange(n_slice).reshape(1, -1)
    gather_inds = np.flatten()

def value_iteration():
    device = 'cpu'
    num_points = 10000 // 50

    n_actions = len(action_list)
    n_base_states = len(state_list)
    n_full_states = n_base_states * num_points
    
    score_by_full_state = torch.arange(0, 10000, 50, device=device).repeat_interleave(len(state_list))

    state_values = torch.zeros((num_points * len(state_list),), device=device)
    state_action_values = torch.zeros((n_full_states, n_actions), device=device)
    print('Computing transition data...')
    pseudo_state_action_table, pseudo_transition_table = compute_transition_data()
    pseudo_transition_table = torch.tensor(pseudo_transition_table, dtype=torch.float32, device=device)
    pseudo_state_action_table = torch.tensor(pseudo_state_action_table, device=device)
    print('Done!')
    state_action_mask = pseudo_state_action_table[:, :, 4]
    full_state_action_mask = torch.tile(state_action_mask, (num_points, 1))

    state_action_gain = pseudo_state_action_table[:, :, 0]
    state_action_episode_end = pseudo_state_action_table[:, :, 3]


    def step_parallel(chunk_size=1000):
        nonlocal state_values
        new_state = torch.zeros_like(state_values)

        index_chunks = torch.arange(n_full_states).split(chunk_size)

        for idx_chunk in tqdm.tqdm(index_chunks):
            actual_chunk_size = idx_chunk.shape[0]
            chunk_state_values = state_values[idx_chunk]
            base_state_idx = idx_chunk % n_base_states

            lost_states = (state_action_gain[base_state_idx]<0)
            ongoing_states = 1-state_action_episode_end[base_state_idx]
            invalid_actions = (state_action_mask[base_state_idx]==0)

            current_score = score_by_full_state[idx_chunk, None] + state_action_gain[base_state_idx]
            # Handling lost states is done explicitly further below
            current_score[lost_states] = 0
            current_score = torch.clip(current_score, max=9950)
            reward = current_score * state_action_episode_end[base_state_idx, :]
            next_state_score_idx = (current_score // 50 * n_base_states)

            gather_inds = next_state_score_idx.reshape(actual_chunk_size, n_actions, 1) + torch.arange(n_base_states, device=device).reshape(1, 1, n_base_states)
            gather_inds = gather_inds.reshape(-1)
            next_state_slice = torch.gather(state_values, dim=0, index=gather_inds).reshape(actual_chunk_size, n_actions, n_base_states)
            future_reward_est = torch.sum(next_state_slice * pseudo_transition_table[base_state_idx], axis=-1)


            next_state_val = reward + future_reward_est * ongoing_states
            next_state_val[lost_states] = 0

            next_state_val[invalid_actions] = -1e4
            state_action_values[idx_chunk] = next_state_val
            new_state[idx_chunk], _ = torch.max(next_state_val, dim=-1)

        diff = torch.max(torch.abs(new_state-state_values))
        print(f'Max Diff: {diff}')
        state_values = new_state
        init_dist = calculate_transition(6, -1)
        print(f'Average case: {np.sum(init_dist * state_values[:n_base_states].to(device="cpu").numpy())}')
        

    for i in range(50):
        step_parallel()

    np.save('resources/state_values.npy', state_values.to(device='cpu').numpy())
    np.save('resources/state_action_values.npy', state_action_values.to(device='cpu').numpy())
    np.save('resources/state_action_mask.npy', full_state_action_mask.to(device='cpu').numpy())

def compute_pick_order(state):
    triplet = state.parent.parent.triplet
    pick_order = []
    
    # If possible, take all
    pick_order.append(state.data)

    # New multiplets
    for i in range(1, 7):
        pick_order.append((i,)*5)

    for i in range(1, 7):
        pick_order.append((i,)*4)

    for i in range(1, 7):
        pick_order.append((i,)*3)

    # Triplet continuation
    if triplet>0:
        pick_order.append((triplet, triplet))
        pick_order.append((triplet,))

    pick_order.append((1,))
    pick_order.append((5,))

    return pick_order

def random_policy(state_idx, score, state_action_table):
    state = state_list[state_idx]
    dice_counts = np.bincount(state.data, minlength=7)
    pick_order = compute_pick_order(state)
    action_mask = state_action_table[:, :, 4]
    state_action_gain = state_action_table[:, :, 0]

    ff_action_idx = [a.pick_inds is None for a in action_list].index(True)
    cashin_action_idx = [a.pick_inds == tuple() for a in action_list].index(True)

    if np.count_nonzero(action_mask[state_idx]) == 1:
        return ff_action_idx

    action_mask[state_idx, ff_action_idx] = 0
    action_idx = np.random.choice(np.nonzero(action_mask[state_idx])[0])
    return action_idx
    
def basic_policy(state_idx, score, state_action_table, action_values):
    state = state_list[state_idx]
    dice_counts = np.bincount(state.data, minlength=7)
    pick_order = compute_pick_order(state)
    action_mask = state_action_table[:, :, 4]
    state_action_gain = state_action_table[:, :, 0]

    ff_action_idx = [a.pick_inds is None for a in action_list].index(True)
    cashin_action_idx = [a.pick_inds == tuple() for a in action_list].index(True)

    if np.count_nonzero(action_mask[state_idx]) == 1:
        return ff_action_idx

    action_idx = -1
    for pick_vals in pick_order:
        if np.any(np.bincount(pick_vals, minlength=7) > dice_counts):
            continue
        data_clone = list(state.data)
        pick_inds = []
        for v in pick_vals:
            pick_ind = data_clone.index(v)
            data_clone[pick_ind] = -1
            pick_inds.append(pick_ind)
        pick_inds = tuple(pick_inds)
        action_idx = [a.pick_inds==pick_inds for a in action_list].index(True)

        if action_mask[state_idx, action_idx]:
            break

    triplet = state.parent.parent.triplet
    pick_vals_bins = np.bincount(pick_vals, minlength=7)
    if np.any(pick_vals_bins>=3):
        triplet = np.argmax(pick_vals_bins)

    real_triplet = triplet in [2, 3, 4, 6]

    new_dice_left = state.parent.dice_left - len(pick_vals)
    max_new_score = score + np.max(state_action_gain[state_idx])

    # if action_values[action_idx] < action_values[cashin_action_idx]:
    #     return cashin_action_idx
    # else:
    #     return action_idx

    if new_dice_left == 0:
        return action_idx
    elif max_new_score >= 1500:
        return cashin_action_idx
    elif max_new_score >= 1000:
        if new_dice_left >= 5 or (triplet in [1, 6] and new_dice_left==3):
            return action_idx
        else:
            return cashin_action_idx
    elif max_new_score >= 300:
        if real_triplet or new_dice_left >= 4:
            return action_idx
        else:
            return cashin_action_idx
    else:
        return action_idx

        

def simulate():
    state_values = np.load('resources/state_values.npy')
    state_action_values = np.load('resources/state_action_values.npy')
    state_action_mask = np.load('resources/state_action_mask.npy')

    n_states = len(state_list)
    n_full_states = state_values.shape[0]

    pseudo_state_action_table, pseudo_transition_table = compute_transition_data()
    valid_moves = (pseudo_state_action_table[:, :, 4]==1) & (pseudo_state_action_table[:, :, 3]==0)
    init_dist = calculate_transition(6, -1)
    state_action_values[state_action_mask==0] = -1e4
    average_case = np.sum(init_dist * state_values[:n_states])
    print(f'Average case: {average_case}')
    
    def single_simulation(silent=False):
        state_idx = np.random.choice(n_states, p=init_dist)
        score = 0
        while True:
            state = state_list[state_idx]
            if not silent:
                print('\n-----------------------\n')
                print(f'Score: {score}')
                print(f'Dice Roll: {state.data}')
                print(f'Running Triples: {state.parent.parent.triplet}')
                print(f'Options:')
            valid_actions = np.nonzero(pseudo_state_action_table[state_idx, :, 4])[0]

            full_state_idx = state_idx + (score // 50 * n_states)
            full_state_idx = np.clip(full_state_idx, 0, n_full_states-1)
            # opt = np.argmax(state_action_values[full_state_idx])
            opt = basic_policy(state_idx, score, pseudo_state_action_table, state_action_values[full_state_idx])

            if not silent:
                for i, action_idx in enumerate(valid_actions):
                    if action_list[action_idx].pick_inds is None:
                        base_msg = f'  {i}: Forfeit'
                    elif len(action_list[action_idx].pick_inds) == 0:
                        base_msg = f'  {i}: Cash In'
                    else:
                        pick_vals = tuple(state.data[j] for j in action_list[action_idx].pick_inds)
                        base_msg = f'  {i}: {pick_vals}'
                    msg = f'{base_msg:20} [Score: {state_action_values[full_state_idx, action_idx]:.0f}]'
                    print(msg)

            # opt = int(input('Pick Option: '))
            # opt = valid_actions[opt]


            if not silent:
                if action_list[opt].pick_inds is None:
                    print(f'  Model Choice: Forfeit')
                elif len(action_list[opt].pick_inds) == 0:
                    print(f'  Model Choice: Cash In')
                else:
                    pick_vals = tuple(state.data[j] for j in action_list[opt].pick_inds)
                    print(f'  Model Choice: {pick_vals}')

            regret = state_action_values[full_state_idx][opt]-np.max(state_action_values[full_state_idx])
            if not silent:
                print(f'  Regret: {regret:.0f}')
                if regret < -50:
                    input('High Regret')
                    


            # input()
            next_dist = pseudo_transition_table[state_idx, opt]
            gain = pseudo_state_action_table[state_idx, opt, 0]
            score += gain
            if action_list[opt].pick_inds is None:
                score = 0

            if pseudo_state_action_table[state_idx, opt, 3]==0:
                state_idx = np.random.choice(n_states, p=next_dist)
            else:
                if not silent:
                    print(f'Finished episode with {score}')
                return score

    scores = []
    while True:
        score = single_simulation(silent=True)
        scores.append(score)
        print(f'Average: {np.mean(scores)}')
        # input()



        
def main():
    # value_iteration()
    simulate()

    state_idx = [n.data==(4,5,5,5) for n in state_list].index(True)
    action_idx = [n.pick_inds==(1, 2, 3) for n in action_list].index(True)
    gain = calculate_gain(state_list[state_idx], (5,5,5))[0]
    print(gain)
    ...

if __name__=='__main__':
    main()

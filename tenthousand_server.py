import os
from pathlib import Path
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
from pydantic import BaseModel

from game_analysis import compute_transition_data, create_state_action_lists

def initialize_app():
    app = FastAPI()

    state_list, action_list = create_state_action_lists()
    state_action_table, _ = compute_transition_data()
    state_action_gain = state_action_table[:, :, 0]

    state_action_values = np.load('resources/state_action_values.npy')
    state_action_mask = np.load('resources/state_action_mask.npy')

    app.state.state_list = state_list
    app.state.action_list = action_list
    app.state.state_action_values = state_action_values
    app.state.state_action_mask = state_action_mask
    app.state.state_action_gain = state_action_gain
    return app

app = initialize_app()

app.mount("/assets", StaticFiles(directory="dice-ui/dist/assets"), name="assets")



class DiceState(BaseModel):
    score: int
    triplet: int
    dice: List[int]


@app.post('/move_overview')
def move_overview(data: DiceState):
    print(f'Incoming Request: {data}')
    score = data.score
    triplet = data.triplet
    dice_values = tuple(sorted(data.dice))

    def valid_state(state):
        return state.parent.parent.triplet==triplet and state.data == dice_values
    
    state_idx = [valid_state(s) for s in app.state.state_list].index(True)
    print(f'Resolved state: {app.state.state_list[state_idx].data}')
    full_state_idx = min(score, 9950) // 50 * len(app.state.state_list) + state_idx
    
    valid_actions = np.flatnonzero(app.state.state_action_mask[full_state_idx])
    print(f'Valid actions: {valid_actions}')
    seen = set()
    moves = []
    best_score = np.max(app.state.state_action_values[full_state_idx])
    for action_idx in valid_actions:
        action_state = app.state.action_list[action_idx]
        print(f'Trying pick: {action_state.pick_inds}')
        if action_state.pick_inds is not None:
            pick_data = tuple(dice_values[i] for i in action_state.pick_inds)
            if pick_data in seen:
                continue
            else:
                seen.add(pick_data)

        if action_state.pick_inds is None:
            action_type = 'forfeit'
        elif len(action_state.pick_inds) == 0:
            action_type = 'cashIn'
        else:
            action_type = 'select'
            dice = pick_data

        expected_score = app.state.state_action_values[full_state_idx, action_idx]
        immediate_score = app.state.state_action_gain[state_idx, action_idx]
        expected_score = float(expected_score)
        immediate_score = float(immediate_score)
        print(f'Expected: {expected_score} | {type(expected_score)}')
        print(f'Imeddiate: {immediate_score} | {type(immediate_score)}')
        p = expected_score / best_score
        if p > 0.9:
            color = 'green'
        elif p > 0.7:
            color = 'yellow'
        elif p > 0.4:
            color = 'orange'
        else:
            color = 'red'
        new_move = {
            'type': action_type,
            'label': '',
            'expectedScore': expected_score,
            'immediateScore': immediate_score,
            'color': color,
        }

        if action_type == 'select':
            new_move['dice'] = dice
        elif action_type == 'forfeit':
            new_move['label'] = 'Forfeit'
        elif action_type == 'cashIn':
            new_move['label'] = 'Cash In'

        moves.append(new_move)

    print('Sending out:')
    print(moves)

    return { 'moves': moves }


    

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    index_path = Path("dice-ui/dist/index.html")
    return FileResponse(index_path)
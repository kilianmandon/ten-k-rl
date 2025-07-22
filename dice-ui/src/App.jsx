import './App.css'
import React, { useState, useEffect } from 'react';
import { Dice1, Dice2, Dice3, Dice4, Dice5, Dice6, RotateCcw, DollarSign, X, Eye, EyeOff, Loader } from 'lucide-react';

const DiceGame = () => {
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [score, setScore] = useState(0);
  const [triplet, setTriplet] = useState(-1);
  const [currentThrow, setCurrentThrow] = useState([null, null, null, null, null, null]);
  const [numDice, setNumDice] = useState(6);
  const [possibleMoves, setPossibleMoves] = useState([]);
  const [isLoadingMoves, setIsLoadingMoves] = useState(false);
  const [selectedMove, setSelectedMove] = useState(null);
  const [selectedDice, setSelectedDice] = useState([false, false, false, false, false, false])
  const [lastState, setLastState] = useState(null);

  const diceComponents = {
    1: Dice1,
    2: Dice2,
    3: Dice3,
    4: Dice4,
    5: Dice5,
    6: Dice6
  };

  const getDiceComponent = (value) => {
    const DiceComp = diceComponents[value];
    return DiceComp ? <DiceComp className="w-12 h-12 text-blue-600" /> : null;
  };

  const getEmptySlots = () => {
    return currentThrow.filter(slot => slot === null).length;
  };

  const addDiceValue = (value) => {
    const emptyIndex = currentThrow.findIndex(slot => slot === null);
    if (emptyIndex !== -1) {
      const newThrow = [...currentThrow];
      newThrow[emptyIndex] = value;
      setCurrentThrow(newThrow);
    }
  };


  const removeDiceAt = (index) => {
    const newThrow = [...currentThrow];
    newThrow[index] = null;
    setCurrentThrow(newThrow);
  };

  const randomThrow = (numDice) => {
      const newThrow = [...currentThrow];
      for (let i = 0; i < numDice; i++) {
        newThrow[i] = Math.floor(Math.random() * 6) + 1;
      }
      for (let i = numDice; i < 6; i++) {
        newThrow[i] = null;
      }
      setCurrentThrow(newThrow);
  };

  const isThrowComplete = () => {
    const filledSlots = currentThrow.filter(slot => slot !== null).length;
    return filledSlots === numDice;
  };

  const getMockMoves = async () => {
    let game_state = {
      score: score,
      triplet: triplet,
      dice: currentThrow.filter(d => d != null)
    }
    const res = await fetch("/move_overview", {
    // const res = await fetch("http://localhost:8000/move_overview", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(game_state)
    });
    const data = await res.json();
    return data.moves;
  };

  useEffect(()=>{
    const newThrow = [...currentThrow];
    for (let i = numDice; i < 6; i++) {
      newThrow[i] = null;
    }
    setCurrentThrow(newThrow);

  }, [numDice]);

  useEffect(() => {
    console.log('Effect triggered.')
    const filledSlots = currentThrow.filter(slot => slot !== null).length;
    console.log(filledSlots);
    console.log(numDice);
    if (isThrowComplete()) {
      setIsLoadingMoves(true);
      setPossibleMoves([]);
      console.log('Retrieving moves.');
      getMockMoves().then(moves => {
        setPossibleMoves(moves);
        setIsLoadingMoves(false);
      });
    } else {
      setPossibleMoves([]);
    }
  }, [currentThrow, numDice]);

  const getButtonColor = (move) => {
    if (!showAnalysis) return 'border-gray-300 hover:bg-gray-100';

    switch (move.color) {
      case 'green': return 'border-green-400 bg-green-50 hover:bg-green-200';
      case 'yellow': return 'border-yellow-400 bg-yellow-50 hover:bg-yellow-200';
      case 'orange': return 'border-orange-400 bg-orange-50 hover:bg-orange-200';
      case 'red': return 'border-red-400 bg-red-50 hover:bg-red-200';
      default: return 'border-gray-300 hover:bg-gray-100';
    }
  };

  const toggleDiceAt = (index) => {
    const newSelected = [...selectedDice];
    newSelected[index] = !newSelected[index];
    setSelectedDice(newSelected);
  };

  const selectMove = (move, index) => {
    setSelectedMove(index);
    let analysis = showAnalysis;
    setShowAnalysis(true);

    setLastState({
      currentThrow, possibleMoves, numDice, triplet, score
    });

    setTimeout(() => {
      // Update game state based on move
      let newNumDice = 6;
      if (move.type === 'cashIn') {
        setScore(prev => 0);
        setTriplet(-1);
      } else if (move.type === 'forfeit') {
        setScore(prev => 0);
        setTriplet(-1);
      } else if (move.type === 'select') {
        setScore(prev => prev + move.immediateScore);
        let counts = [0, 0, 0, 0, 0, 0]
        move.dice.forEach(v => counts[v-1] += 1);
        console.log('Counts');
        console.log(counts);

        let max_idx = counts.indexOf(Math.max(...counts));
        if (numDice==move.dice.length) {
          newNumDice = 6;
          setTriplet(-1);
        } else {
          newNumDice = numDice - move.dice.length;
          if (counts[max_idx] >= 3) {
            setTriplet(max_idx+1);
            console.log(`Setting triplet to ${max_idx+1}`);
          }

        }
      }

      // Reset for next turn
      setShowAnalysis(analysis);
      setSelectedDice([false, false, false, false, false, false]);
      setPossibleMoves([]);
      setSelectedMove(null);
      if (showManualEntry) {
        setCurrentThrow([null, null, null, null, null, null]);
      } else {
        randomThrow(newNumDice);
      }
      setNumDice(newNumDice);

      // Scroll to top
      // window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 1000);
  };

  const undoButton = () => {
    return <button
      onClick={() => {
        setNumDice(lastState.numDice);
        setScore(lastState.score);
        setTriplet(lastState.triplet);
        setCurrentThrow(lastState.currentThrow);
        setPossibleMoves(lastState.possibleMoves);
        setLastState(null);
      }}
      className="w-full bg-gray-100 text-gray-600 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
    >
      Undo
    </button>
  }

  const resetGame = (currentThrow, selectedDice) => {
    setScore(0);
    setTriplet([]);
    setCurrentThrow([null, null, null, null, null, null]);
    setSelectedDice([false, false, false, false, false, false]);
    setNumDice(6);
    setPossibleMoves([]);
    setSelectedMove(null);
  };

  const renderMoveAccepting = () => {
    const arrayEquals = (a, b) => {
      return a.length === b.length &&
        a.every((val, index) => val === b[index]);
    }

    if (possibleMoves.length == 1) {
      let move = possibleMoves[0];
      let index = 0;
      return <button
        key={`forfeit-${index}`}
        onClick={() => selectMove(move, `forfeit-${index}`)}
        className={`w-full p-4 border-2 rounded-lg flex items-center justify-between transition-all ${getButtonColor(move)}  ${!showAnalysis ? 'justify-center' : ''}`}
      >
        <div className="flex items-center gap-3">
          <X className="w-5 h-5 text-red-600" />
          <span className="font-medium">{move.label}</span>
        </div>
        {showAnalysis && (
          <span className="text-sm text-gray-600">
            Expected: {Math.round(move.expectedScore)}
          </span>
        )}
      </button>
    } else if (!selectedDice.some(a => a)) {
      let move = possibleMoves.filter(m => m.type === 'cashIn')[0];
      console.log(`Move: ${move.dice}`)
      let index = 0;
      return <button
        key={`cashIn-${index}`}
        onClick={() => selectMove(move, `cashIn-${index}`)}
        className={`w-full p-4 border-2 rounded-lg flex items-center justify-between transition-all ${selectedMove === `cashIn-${index}` ? 'bg-blue-200 border-blue-500' : getButtonColor(move)
          }  ${!showAnalysis ? 'justify-center' : ''}`}
      >
        <div className="flex items-center gap-3">
          <DollarSign className="w-5 h-5 text-green-600" />
          <span className="font-medium">{move.label}</span>
        </div>
        {showAnalysis && (
          <span className="text-sm text-gray-600">
            Expected: {Math.round(move.expectedScore)}
          </span>
        )}
      </button>
    } else {
      let selectMoves = possibleMoves.filter(m => m.type === 'select');
      let selectedValues = currentThrow.filter((v, i) => selectedDice[i]).toSorted();
      let index = selectMoves.findIndex(move => arrayEquals(move.dice.toSorted(), selectedValues));
      if (index < 0) {
        return <button
          key={`select-${index}`}
          disabled
          className={`w-full p-4 border-2 rounded-lg flex items-center justify-center transition-all`}
        >
          <div className="flex items-center gap-3">
            <span className="font-medium">Invalid</span>
          </div>
        </button>

      }
      let move = selectMoves[index];

      return <button
        key={`select-${index}`}
        onClick={() => selectMove(move, `select-${index}`)}
        className={`w-full p-4 border-2 rounded-lg flex items-center justify-between transition-all ${getButtonColor(move)} ${!showAnalysis ? 'justify-center' : ''}`}
      >
        <div className={`flex items-center gap-3`}>
          <div className="flex gap-1">
            {move.dice.map((dice, diceIndex) => (
              <div key={diceIndex} className="flex items-center justify-center">
                <div className="w-8 h-8 flex items-center justify-center">
                  {React.createElement(diceComponents[dice], { className: "w-8 h-8 text-blue-600" })}
                </div>
              </div>
            ))}
          </div>
          <span className="font-medium">{move.label}</span>
        </div>
        {showAnalysis && (
          <span className="text-sm text-gray-600">
            Expected: {Math.round(move.expectedScore)}
          </span>
        )}
      </button>

    }

  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-bold text-gray-800">Dice Game</h1>
            <button
              onClick={() => setShowAnalysis(!showAnalysis)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${showAnalysis
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600'
                }`}
            >
              {showAnalysis ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              Analysis {showAnalysis ? 'ON' : 'OFF'}
            </button>

          </div>

          <div className="flex justify-between">
          <button
            onClick={resetGame}
            className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg text-sm text-gray-600 hover:bg-gray-200 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Reset Game
          </button>
          <button
              onClick={() => setShowManualEntry(!showManualEntry)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${showManualEntry
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600'
                }`}
            >
              Random {!showManualEntry ? 'ON' : 'OFF'}
            </button>
            </div>
        </div>

        {/* Game State */}
        <div className="min-h-screen">
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
            <div className="text-center mb-6">
              <div className="text-sm text-gray-600 mb-2">Current Score</div>
              <div className="text-4xl font-bold text-blue-600">{score}</div>
            </div>

            {/* Triplets */}
            {triplet > 0 && (
              <div className="mb-6">
                <div className="text-sm text-gray-600 mb-3 text-center">Triplet</div>
                <div className="flex justify-center gap-4">
                    <div  className="flex gap-1">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="p-1 border-gray-300 rounded w-8 h-8">
                          {React.createElement(diceComponents[triplet], { className: "w-8 h-8 text-blue-600" })}
                        </div>
                      ))}
                    </div>
                </div>
              </div>
            )}

            {/* Throw Controls */}
            <div className="space-y-3">
              {!showManualEntry && <button
                onClick={() => randomThrow(numDice)}
                className="w-full bg-blue-500 text-white py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors"
              >
                🎲 Random Throw
              </button>}

              {showManualEntry && <div className="grid grid-cols-3 gap-2">
                {[1, 2, 3, 4, 5, 6].map(value => (
                  <button
                    key={value}
                    onClick={() => addDiceValue(value)}
                    disabled={getEmptySlots() === 0}
                    className="flex items-center justify-center py-3 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {getDiceComponent(value)}
                  </button>
                ))}
              </div>}
              <button
                onClick={() => setCurrentThrow(currentThrow.map(() => null))}
                className="w-full bg-gray-100 text-gray-600 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
              >
                Clear
              </button>
              


            {/* Current Throw */}
            <div className="mb-6 flex items-center flex-col">
              <div className="text-sm text-gray-600 mb-3 text-center">
                Throw ({numDice} dice)
              </div>
              <div className="flex flex-wrap justify-center gap-2 mb-4"
                style={{ width: 'max-content', maxWidth: 'calc(3 * 4rem + 2 * 0.5rem)' }}>
                {currentThrow.slice(0, numDice).map((dice, index) => (
                  <button
                    key={index}
                    onClick={() => dice && toggleDiceAt(index)}
                    className={`w-16 h-16 border-2 border-dashed rounded-lg flex items-center justify-center transition-all ${dice
                      ? 'border-blue-300 bg-blue-50 hover:bg-blue-100'
                      : 'border-gray-300 bg-gray-50'
                      } ${selectedDice[index] ? 'border-solid border-green-300' : ''}`}
                  >
                    {dice ? getDiceComponent(dice) : <div className="w-3 h-3 bg-gray-300 rounded-full" />}
                  </button>
                ))}
              </div>
            </div>
            </div>

            <div className="space-y-3">
            {possibleMoves.length > 0 &&
                renderMoveAccepting(currentThrow, selectedDice)

              }
              {lastState != null && undoButton()}
              </div>
            
          </div>
        </div>
      </div>

      {/* Moves Area */}
      {(isLoadingMoves || possibleMoves.length > 0) && (
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="text-lg font-semibold text-gray-800 mb-4 text-center">
            Possible Moves
          </div>

          {isLoadingMoves ? (
            <div className="flex items-center justify-center py-8">
              <Loader className="w-8 h-8 animate-spin text-blue-500" />
              <span className="ml-3 text-gray-600">Loading moves...</span>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Cash In - Always at top */}
              {possibleMoves.filter(m => m.type === 'cashIn').map((move, index) => (
                <button
                  key={`cashIn-${index}`}
                  onClick={() => selectMove(move, `cashIn-${index}`)}
                  className={`w-full p-4 border-2 rounded-lg flex items-center justify-between transition-all ${selectedMove === `cashIn-${index}` ? 'bg-blue-200 border-blue-500' : getButtonColor(move)
                    }`}
                >
                  <div className="flex items-center gap-3">
                    <DollarSign className="w-5 h-5 text-green-600" />
                    <span className="font-medium">{move.label}</span>
                  </div>
                  {showAnalysis && (
                    <span className="text-sm text-gray-600">
                      Expected: {Math.round(move.expectedScore)}
                    </span>
                  )}
                </button>
              ))}

              {/* Select moves */}
              {possibleMoves.filter(m => m.type === 'select').map((move, index) => (
                <button
                  key={`select-${index}`}
                  onClick={() => selectMove(move, `select-${index}`)}
                  className={`w-full p-4 border-2 rounded-lg flex items-center justify-between transition-all ${selectedMove === `select-${index}` ? 'bg-blue-200 border-blue-500' : getButtonColor(move)
                    }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex gap-1">
                      {move.dice.map((dice, diceIndex) => (
                        <div key={diceIndex} className="flex items-center justify-center">
                          <div className="w-8 h-8 flex items-center justify-center">
                            {React.createElement(diceComponents[dice], { className: "w-8 h-8 text-blue-600" })}
                          </div>
                        </div>
                      ))}
                    </div>
                    <span className="font-medium">{move.label}</span>
                  </div>
                  {showAnalysis && (
                    <span className="text-sm text-gray-600">
                      Expected: {Math.round(move.expectedScore)}
                    </span>
                  )}
                </button>
              ))}

              {/* Forfeit - Always at bottom */}
              {possibleMoves.filter(m => m.type === 'forfeit').map((move, index) => (
                <button
                  key={`forfeit-${index}`}
                  onClick={() => selectMove(move, `forfeit-${index}`)}
                  className={`w-full p-4 border-2 rounded-lg flex items-center justify-between transition-all ${selectedMove === `forfeit-${index}` ? 'bg-blue-200 border-blue-500' : getButtonColor(move)
                    }`}
                >
                  <div className="flex items-center gap-3">
                    <X className="w-5 h-5 text-red-600" />
                    <span className="font-medium">{move.label}</span>
                  </div>
                  {showAnalysis && (
                    <span className="text-sm text-gray-600">
                      Expected: {Math.round(move.expectedScore)}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DiceGame;
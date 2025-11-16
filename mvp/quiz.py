import json
from typing import Callable, Dict, Optional

TutorCallback = Callable[[Dict[str,str],str], Optional[str]]

def run_quiz(lessoncontent: list, input_fn=input, print_fn=print, tutor_callback : Optional[TutorCallback] = None) -> int:
    """
    
    """
    coins = 0   
    quizzes= [data for data in lessoncontent if data.get("TYPE") == "QUIZ"]

    if len(quizzes) == 0:
      print("ERROR 404, self destruct imminent")
      return 0
    quiz = quizzes[0]
    questions = quiz["QUESTIONS"]

    for q in questions:
        print_fn(f'\nQ{q["QUESTION_NUMBER"]}. {q["QUESTION"]}')
        for option_key in ["A", "B", "C", "D"]:
            # TODO: 
            print_fn(f'{option_key} {q["OPTIONS"][option_key]}')
          
        answer = input_fn("> :").strip().upper()
        while answer not in ["A","B","C","D"]:
            print_fn("Please enter A, B, C, or D")
            answer = input_fn("> :").strip().upper()
            continue
        if answer == q["CORRECT_ANSWER"]:
            coins += 10
            print_fn("Correct: +10 coins")
        else:
            coins -= 5
            print_fn("Incorrect: -5 coins")
            if tutor_callback:
                feedback = tutor_callback(q, answer)
                if feedback:
                    printable = feedback if isinstance(feedback, str) else json.dumps(feedback, indent=2)
                    print_fn("\nAI Tutor:")
                    print_fn(printable)


    
    return coins

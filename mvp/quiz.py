from openai import OpenAI
import ai_wrapper

def run_quiz(lessoncontent: list, input_fn=input, print_fn=print) -> int:
    """
    
    """
    coins = 0   
    quizzes= []
    for data in lessoncontent:
        if data.get("TYPE") == "QUIZ":
            quizzes.append(data)

    if len(quizzes) == 0:
      print("ERROR 404, self destruct imminent")
      return 0
    quiz = quizzes[0]
    questions = quiz["QUESTIONS"]

    for q in questions:
        print_fn(f'\nQ{q["QUESTION_NUMBER"]}. {q["QUESTION"]}')
        options = q["OPTIONS"]
        for i in ["A","B","C","D"]:
            print_fn(f'{i} {options[i]}')
          
        answer = input_fn("> :").strip().upper()
        while answer not in ["A","B","C","D"]:
            print_fn("Please enter A, B, C, or D")
            answer = input_fn("> :").strip().upper()
            continue
      
      if answer
            

    
    return coins
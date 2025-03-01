import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_question = questions[start:end]

    return current_question

def create_app(db_URI="", test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    TODO: Done
    """
    CORS(app, resources={"/": {"origins": "*"}})

    if db_URI:
        setup_db(app,db_URI)
    else:
        setup_db(app)

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    TODO: Done
    """
    @app.after_request
    def after_request(response):

        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
             "Access-Control-Allow-Methods", "GET,POST,DELETE"
        )

        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route("/categories")
    def get_categories():
        
        try:

            # get all categories and add to dict
            categories = Category.query.order_by(Category.id).all()

            if categories:
                dict = {}
                
                for category in categories:
                    dict[category.id] = category.type

                # return jsonified data
                return jsonify(
                    {
                    'categories': dict
                    }
            )
        
        except Exception as e:
                print(e)
                abort(404)
    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route("/questions")
    def get_questions():

        # get all questions
        questions = Question.query.order_by(Question.id).all()
        
        # get all categories
        categories = Category.query.order_by(Category.id).all()

        # get the current questions on the page
        current_question = paginate_questions(request, questions)

        if len(current_question) == 0:
            abort (404)
        
        # add all categories to a dict
        if categories:
            dict = {}
            
            for category in categories:
                dict[category.id] = category.type
        
        # return jsonified data
        return jsonify(
            {
                'questions': current_question,
                'total_questions': len(questions),
                'categories': dict,
                'current_category': category.type
            }
        )

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):
        
        # get specified question
        question = Question.query.get(id)

        if question:
            
            # delete specified question
            question.delete()

            # return jsonified data
            return jsonify(
                {
                    'deleted': question.id
                }
            )
        
        # abort 404 if question cannot be deleted   
        else:
            abort(404)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=['POST'])
    def add_question():

        # retrieve body 
        body = request.get_json()

        # get new data
        new_question = body.get('question')
        new_answer = body.get('answer')
        new_category = body.get('category')
        new_difficulty = body.get('difficulty')

        # abort 422 if conditions are not met
        if ((len(new_question) == 0) or (len(new_answer) == 0) or (new_category not in range(7)) or (new_difficulty not in range(6))):    
            abort(422)
        
        else:
            # add new question
            question = Question(
                question = new_question,
                answer = new_answer,
                category = new_category,
                difficulty = new_difficulty
            )
            
            question.insert()

            # get all questions
            selection = Question.query.order_by(Question.id).all()

            # paginate specified selection 
            current_question = paginate_questions(request, selection)

            # get the total number of questions
            total_questions = len(selection)

            # return jsonified data
            return jsonify(
                {
                    'created': question.id,
                    'questions': current_question,
                    'total_questions': total_questions
                }
            )

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        
        # retrieve body 
        body = request.get_json()

        # get search term
        search = body.get('searchTerm', None)

        # Select all questions case insensitive that contain search term
        selection = Question.query.filter(
            Question.question.ilike('%{}%'.format(search))).all()

        if selection:

            # paginate specified questions
            current_questions = paginate_questions(request, selection)
            
            # return jsonified data
            return jsonify(
                {
                    'questions': current_questions,
                    'total_questions': len(selection)
                }
            )
        
        # abort 404 if selection not found
        else:
            abort(404)
        

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/categories/<int:id>/questions')
    def questions_in_category(id):

        # get category with specified id
        category = Category.query.filter(Category.id == id).one_or_none()
        
        # abort 404 if category not found
        if (category is None):
            abort (404)

        else:   
            #select all questions in specified category
            selection = Question.query.filter_by(category = id).all()

            # paginate specified questions
            current_questions = paginate_questions(request, selection)

            # return jsonfied data
            return jsonify({
                'questions': current_questions,
                'total_questions': len(selection),
                'current_category': category.type
            })

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route('/quizzes', methods=['POST'])
    def quiz():
        try:
            # retrieve body
            body = request.get_json()

            # retrieve the previous question
            previous_questions = body.get('previous_questions', None)

            # retireve quiz category
            quiz_category = body.get('quiz_category', None)

            if (quiz_category['id'] == 0):

                # return all questions
                questions = Question.query.all()

            else:
            
            # return questions filtered by category
                questions = Question.query.filter_by(
                    category=quiz_category['id']).all()

            # generates random questions
            def get_random_question():
                next_question = random.choice(questions)
                return next_question

            # get random question for next question
            next_question = get_random_question()

            # check if question was previously asked with boolean
            question_found = True

            while question_found:

                if next_question.id in previous_questions:
                    next_question = get_random_question()
                else:
                    question_found = False

            # return jsonfied data
            return jsonify(
                {
                'question': next_question.format(),
                }
            )
        # abort 422 if exception
        except Exception as e:
            print (e)
            abort(422)
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    # Error handler for Bad request
    @app.errorhandler(400)
    def err_bad_request(error):
        data = {
            'error': 400,
            'message': 'bad request'
        }
        return jsonify(data), 400

    # Error handler for resource not found
    @app.errorhandler(404)
    def err_not_found(error):
        data = {
            'error': 404,
            'message': 'resource not found'
        }
        return jsonify(data), 404
    
    # Error handler for unprocesable entity
    @app.errorhandler(422)
    def err_unprocessable(error):
        data = {
            'error': 422,
            'message': 'unprocessable'
        }
        return jsonify(data), 422

    return app


from flask import Blueprint, request, jsonify, session, Response
from models import db, User, Expense, ExpenseParticipant, SplitMethod
from sqlalchemy import func
import csv

from enum import Enum

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/register', methods=['POST'])
def register():
    """
    This route is for new users to sign up.
    
    Users must provide their name, email, phone number, and password.
    If the registration is successful, the user is added to the database.
    
    Returns:
        JSON response with a success message and status code 201.
    """
    data = request.get_json()  # get the info from user
    new_user = User(name=data['name'], email=data['email'], phone=data['phone'], password=data['password'])
    
    db.session.add(new_user)  # put new user in the database
    db.session.commit()  # save it
    
    return jsonify({'message': 'User registered successfully!'}), 201

@api_blueprint.route('/login', methods=['POST'])
def login():
    """
    This route allows users to log in using their email and password.
    
    If the credentials are valid, the user's ID is stored in the session.
    A success message with user details is returned if login is successful,
    otherwise an error message is returned.
    
    Returns:
        JSON response with a success message and user details, or an error message.
    """
    data = request.get_json()  # get info from user
    user = User.query.filter_by(email=data['email'], password=data['password']).first()  # find user
    
    if user:
        session['user_id'] = user.id  # save user ID in session
        return jsonify({'message': 'Login successful!', 'user': {'name': user.name, 'email': user.email}}), 200
    else:
        return jsonify({'message': 'Invalid credentials!'}), 401 

@api_blueprint.route('/users', methods=['GET'])
def get_users():
    """
    This route returns a list of all registered users.
    
    It includes the user ID, name, email, and phone number for each user.
    
    Returns:
        JSON response with a list of user details and status code 200.
    """
    users = User.query.all()  # get all users from database
    return jsonify([{'id': user.id, 'name': user.name, 'email': user.email, 'phone': user.phone} for user in users]), 200




@api_blueprint.route('/expenses', methods=['POST'])
def add_expense():
    """
    Add a new expense and split it among participants.
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Please log in first'}), 401

    data = request.get_json()
    creator_id = session['user_id']
    
    new_expense = Expense(
        description=data['description'],
        amount=data['amount'],
        split_method=SplitMethod(data['split_method']),
        created_by=creator_id
    )
    db.session.add(new_expense)
    db.session.flush()  # This assigns an ID to new_expense

    participants = data['participants']
    
    # Ensure the creator is in the participants list
    if not any(p['user_id'] == creator_id for p in participants):
        participants.append({'user_id': creator_id})

    total_share = 0

    for participant in participants:
        user = User.query.get(participant['user_id'])
        if not user:
            db.session.rollback()
            return jsonify({'message': f"User with id {participant['user_id']} not found"}), 404

        if new_expense.split_method == SplitMethod.EQUAL:
            share = new_expense.amount / len(participants)
        elif new_expense.split_method == SplitMethod.EXACT:
            share = participant.get('share', new_expense.amount / len(participants))
        elif new_expense.split_method == SplitMethod.PERCENTAGE:
            share = new_expense.amount * (participant.get('share', 100 / len(participants)) / 100)

        total_share += share

        expense_participant = ExpenseParticipant(
            expense_id=new_expense.id,
            user_id=participant['user_id'],
            share=share
        )
        db.session.add(expense_participant)

    if abs(total_share - new_expense.amount) > 0.01:  # Allow for small float rounding errors
        db.session.rollback()
        return jsonify({'message': 'The sum of shares does not match the total amount'}), 400

    db.session.commit()
    return jsonify({'message': 'Expense added successfully', 'expense_id': new_expense.id}), 201


@api_blueprint.route('/expenses/user', methods=['GET'])
def get_user_expenses():
    """
    Retrieve all expenses for the logged-in user.
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Please log in first'}), 401

    user_id = session['user_id']
    user_expenses = ExpenseParticipant.query.filter_by(user_id=user_id).all()
    
    expenses = []
    for participant in user_expenses:
        expense = Expense.query.get(participant.expense_id)
        expenses.append({
            'id': expense.id,
            'description': expense.description,
            'amount': expense.amount,
            'split_method': expense.split_method.value,
            'created_by': expense.created_by,
            'created_at': expense.created_at,
            'user_share': participant.share
        })

    return jsonify(expenses), 200

@api_blueprint.route('/expenses', methods=['GET'])
def get_all_expenses():
    """
    Retrieve all expenses that the logged-in user is involved in.
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Please log in first'}), 401

    user_id = session['user_id']

    # Get all expenses where the user is either the creator or a participant
    user_expenses = db.session.query(Expense).join(ExpenseParticipant).filter(
        (Expense.created_by == user_id) | (ExpenseParticipant.user_id == user_id)
    ).distinct().all()

    expenses = []
    for expense in user_expenses:
        participants = ExpenseParticipant.query.filter_by(expense_id=expense.id).all()
        expenses.append({
            'id': expense.id,
            'description': expense.description,
            'amount': expense.amount,
            'split_method': expense.split_method.value,
            'created_by': expense.created_by,
            'created_at': expense.created_at,
            'participants': [{'user_id': p.user_id, 'share': p.share} for p in participants]
        })

    return jsonify(expenses), 200


@api_blueprint.route('/balance', methods=['GET'])
def get_balance():
    """
    Generate a balance sheet for each expense for the logged-in user,
    including total amount, payer, and how much it is split between members.
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Please log in first'}), 401

    user_id = session['user_id']

    # Get all expenses where the user is either the creator or a participant
    user_expenses = db.session.query(Expense).join(ExpenseParticipant).filter(
        (Expense.created_by == user_id) | (ExpenseParticipant.user_id == user_id)
    ).distinct().all()

    balance_sheet = []
    for expense in user_expenses:
        participants = ExpenseParticipant.query.filter_by(expense_id=expense.id).all()
        total_amount = expense.amount
        payer = expense.created_by
        
        # Create a list of participants with their shares
        shares = [{'user_id': p.user_id, 'share': p.share} for p in participants]

        balance_sheet.append({
            'expense_id': expense.id,
            'description': expense.description,
            'total_amount': total_amount,
            'payer': payer,
            'shares': shares,
            'created_at': expense.created_at
        })

    return jsonify(balance_sheet), 200


@api_blueprint.route('/balance/download', methods=['GET'])
def download_balance_sheet():
    """
    Generate a downloadable balance sheet for the logged-in user in CSV format.
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Please log in first'}), 401

    user_id = session['user_id']

    # Get all expenses where the user is either the creator or a participant
    user_expenses = db.session.query(Expense).join(ExpenseParticipant).filter(
        (Expense.created_by == user_id) | (ExpenseParticipant.user_id == user_id)
    ).distinct().all()

    if not user_expenses:
        return jsonify({'message': 'No expenses found for download.'}), 404

    # Create a CSV response
    def generate_csv():
        yield "Expense ID,Description,Total Amount,Payer,User ID,Share,Created At\n"  # CSV Header
        for expense in user_expenses:
            participants = ExpenseParticipant.query.filter_by(expense_id=expense.id).all()
            payer = expense.created_by
            for participant in participants:
                yield f"{expense.id},{expense.description},{expense.amount},{payer},{participant.user_id},{participant.share},{expense.created_at}\n"

    return Response(generate_csv(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=balance_sheet.csv"})

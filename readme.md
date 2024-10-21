
# Expense Sharing API
This is an expense sharing API made in Python Flask<br>
This API provides essential features for creating and managing shared expenses. It supports user registration, logging in, and tracking expenses among participants.

## Key Features
- User Registration and Login
- Expense creation and sharing among participants
- Retrieval of user-specific and general expenses
- Balance calculation for individual users

## API Endpoints

### 1. Register User
- **Method**: POST
- **URL**: `http://127.0.0.1:5000/register`
- **Description**: This endpoint registers a new user in the system. Users must provide their name, email, phone number, and password.
- **Body** (raw):
  ```json
  {
    "name": "bob",
    "email": "bob@test.com",
    "phone": "1234567870",
    "password": "pass123"
  }
  ```
- **Response**:
  ```json
  {
    "message": "User registered successfully!"
  }
  ```

### 2. Get Users
- **Method**: GET
- **URL**: `http://127.0.0.1:5000/users`
- **Description**: Retrieves a list of all registered users including their ID, name, email, and phone number.
- **Response**:
  ```json
  [
    {
      "email": "jane@test.com",
      "id": 1,
      "name": "jane",
      "phone": "1234567890"
    },
    {
      "email": "alice@test.com",
      "id": 2,
      "name": "alice",
      "phone": "1234567880"
    }
  ]
  ```

### 3. Login User
- **Method**: POST
- **URL**: `http://127.0.0.1:5000/login`
- **Description**: Allows users to log in using their email and password. If successful, stores the user's ID in the session.
- **Body** (raw):
  ```json
  {
    "email": "jane@test.com",
    "password": "pass123"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Login successful!",
    "user": {
      "email": "jane@test.com",
      "name": "jane"
    }
  }
  ```

### 4. Add Expense
- **Method**: POST
- **URL**: `http://127.0.0.1:5000/expenses`
- **Description**: Adds a new expense and splits it among participants. Users must be logged in to add an expense.
It will return an error if in the percentage and equal method the total percentage is not 100 and the amount of sum is not equal to the expense amount.
- **Body** (raw):
  ```json
  {
    "description": "vada pao",
    "amount": 30,
    "split_method": "equal",
    "participants": [
      {"user_id": 2},
      {"user_id": 3}
    ]
  }
  ```
- **Response**:
  ```json
  {
    "expense_id": 3,
    "message": "Expense added successfully"
  }
  ```

### 5. Get User Expenses
- **Method**: GET
- **URL**: `http://127.0.0.1:5000/expenses/user`
- **Description**: Retrieves all expenses for the logged-in user. Users must be logged in to see their expenses.
- **Response**:
  ```json
  [
    {
      "amount": 75,
      "created_at": "Sun, 20 Oct 2024 04:31:01 GMT",
      "created_by": 1,
      "description": "Monthly Rent",
      "id": 1,
      "split_method": "equal",
      "user_share": 25
    }
  ]
  ```

### 6. Get All Expenses
- **Method**: GET
- **URL**: `http://127.0.0.1:5000/expenses`
- **Description**: Retrieves all expenses that the logged-in user is involved in.
- **Response**:
  ```json
  [
    {
      "amount": 75,
      "description": "Monthly Rent",
      "participants": [
        {"share": 25, "user_id": 2},
        {"share": 25, "user_id": 3}
      ]
    }
  ]
  ```


## License
This project is licensed under the MIT License - see the LICENSE file for details.

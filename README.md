# Flask-MongoDB Web App

# FitLogix: User Management and Fitness Tracker Application

## Overview

This application is a Flask-based web service designed to handle user management and fitness tracking. It utilizes MongoDB for data storage and provides several web routes to interact with the user interface and the database. The application includes features for user registration, login, and session management, as well as functionalities to create, read, update, and delete fitness-related data.

## Features

### User Authentication
- **Sign Up**: Users can register by providing a username and password. The application checks for the uniqueness of the username and stores the user data securely in MongoDB.
- **Login**: Users can log in using their credentials. Upon successful authentication, they are redirected to the home page.
- **Logout**: Authenticated users can log out of the application, which clears their session.


### Fitness Data Management
- **Create Records**: Users can add new fitness records specifying details such as date, body part focused, exercises performed, reps, and weight.
- **Read Records**: Users can view all their fitness records sorted by date in descending order.
- **Update Records**: Users can edit existing fitness records by modifying any aspect of their exercise logs.
- **Delete Records**: Users can delete any fitness record using its MongoDB ObjectId.

    
## Note 

I was not able to host the website on the i6 server. I will be sending the .env file on the chat.



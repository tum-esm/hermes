#!/bin/bash

# fetch username and password from user input
echo "Enter server url: "
read server
echo "Enter username: "
read username
echo "Enter password: "
read password

# Create a new user
curl -X POST -H "Content-Type: application/json" -d '{"user_name": "'$username'", "password": "'$password'"}' $server/users

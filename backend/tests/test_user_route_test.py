# def test_get_current_user(
#     test_client_authenticated_default: TestClient,
#     user_read: UserRead
# ):
#     """Should return the current authenticated user"""
#     test_client = test_client_authenticated_default

#     response = test_client.get("/me")

#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()["status"] == 200
#     assert response.json()["message"] == "Current user retrieved"
#     assert response.json()["data"] == user_read


# def test_update_current_user(
#     test_client_authenticated_default: TestClient,
#     user_update_me: UserUpdateMe,
#     user_read: UserRead,
#     db_session: Session
# ):
#     """Should update the current authenticated user"""
#     test_client = test_client_authenticated_default

#     response = test_client.put("/me", json=user_update_me)

#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()["status"] == 200
#     assert response.json()["message"] == "Current user updated"
#     assert response.json()["data"] == user_read

#     with db_session as session:
#         updated_user = session.get(User, user_read.id)

#         assert updated_user.username == user_update_me.username
#         assert updated_user.email == user_update_me.email
#         assert updated_user.full_name == user_update_me.full_name


# def test_get_user(
#     test_client_authenticated_default: TestClient,
#     user_read: UserRead,
#     db_session: Session
# ):
#     """Should return a user by their ID"""
#     test_client = test_client_authenticated_default

#     response = test_client.get(f"/{user_read.id}")

#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()["status"] == 200
#     assert response.json()["message"] == "User retrieved"
#     assert response.json()["data"] == user_read


# def test_get_all_users(
#     test_client_authenticated_default: TestClient,
#     user_list_response: UserListResponse
# ):
#     """Should return all users"""
#     test_client = test_client_authenticated_default

#     response = test_client.get("/")

#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()["status"] == 200
#     assert response.json()["message"] == "Users retrieved"
#     assert response.json()["data"] == user_list_response


# def test_update_user(
#     test_client_authenticated_default: TestClient,
#     user_update: UserUpdate,
#     user_read: UserRead,
#     db_session: Session
# ):
#     """Should update a user"""
#     test_client = test_client_authenticated_default

#     response = test_client.put(f"/{user_read.id}", json=user_update)

#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()["status"] == 200
#     assert response.json()["message"] == "User updated"
#     assert response.json()["data"] == user_read

#     with db_session as session:
#         updated_user = session.get(User, user_read.id)

#         assert updated_user.username == user_update.username
#         assert updated_user.email == user_update.email
#         assert updated_user.full_name == user_update.full_name


# def test_delete_user(
#     test_client_authenticated_default: TestClient,
#     user_read: UserRead,
#     db_session: Session
# ):
#     """Should delete a user"""
#     test_client = test_client_authenticated_default

#     response = test_client.delete(f"/{user_read.id}")

#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()["status"] == 200
#     assert response.json()["message"] == "User deleted"

#     with db_session as session:
#         deleted_user = session.get(User, user_read.id)

#         assert deleted_user is None

import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GridSearchCV

# Train the model on train.csv file
train_df = pd.read_csv('train.csv')
train_df.dropna(inplace=True)

X_train = train_df.drop(['is_canceled'], axis=1)
y_train = train_df['is_canceled']

categorical_cols = X_train.select_dtypes(include=['object']).columns
for col in categorical_cols:
    le = LabelEncoder()
    X_train[col] = le.fit_transform(X_train[col])
    
# Handle missing values by imputing with the mean value
imputer = SimpleImputer(strategy='mean')
X_train = imputer.fit_transform(X_train)

# Define the decision tree classifier
clf = DecisionTreeClassifier()

# Define the hyperparameters to tune
params = {'max_depth': [3, 5, 10, None], 'min_samples_split': [2, 5, 10], 'min_samples_leaf': [1, 2, 4]}

# Use GridSearchCV to find the best hyperparameters
grid_search = GridSearchCV(clf, param_grid=params, cv=5)
grid_search.fit(X_train, y_train)

# Print the best hyperparameters
print("Best hyperparameters:", grid_search.best_params_)

# Test the model on test.csv file
test_df = pd.read_csv('test.csv')
test_df_copy = test_df.copy() # create a copy of test_df
test_id = test_df['id']
test_df_copy = test_df_copy.drop(['Unnamed: 32', 'Unnamed: 33'], axis=1)

categorical_cols = test_df_copy.select_dtypes(include=['object']).columns
for col in categorical_cols:
    le = LabelEncoder()
    test_df_copy[col] = le.fit_transform(test_df_copy[col])

# Handle missing values in test dataset by imputing with the mean value
test_df_copy = imputer.transform(test_df_copy)

# Use the best hyperparameters to fit the model
clf_best = DecisionTreeClassifier(**grid_search.best_params_)
clf_best.fit(X_train, y_train)

y_pred_train = clf_best.predict(X_train)
y_pred_test = clf_best.predict(test_df_copy)

# Calculate the train and test accuracy
train_accuracy = sum(y_pred_train == y_train) / len(y_train)
print("Train accuracy:", train_accuracy)

submission_df = pd.DataFrame({'Id': test_id, 'Is_canceled': y_pred_test})
submission_df.to_csv('submission_final_2.csv', index=False)

import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.impute import SimpleImputer

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

clf = DecisionTreeClassifier()
clf.fit(X_train, y_train)

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

y_pred = clf.predict(test_df_copy)

# Generate submission.csv file
submission_df = pd.DataFrame({'Id': test_id, 'Is_canceled': y_pred})
submission_df.to_csv('submission_final.csv', index=False)
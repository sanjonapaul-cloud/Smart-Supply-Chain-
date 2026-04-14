import pandas as pd
from sklearn.linear_model import LogisticRegression
import pickle

# load dataset
data = pd.read_csv("data/dataset.csv")

X = data[["distance", "delay", "weather"]]
y = data["risk"]

# train model
model = LogisticRegression()
model.fit(X, y)

# save model
pickle.dump(model, open("models/model.pkl", "wb"))

print("Model trained and saved!")
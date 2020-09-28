#import the necessary module
import pandas as pd
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
#split data set into train and test setsdata_train, data_test, target_train, target_test = train_test_split(data,target, test_size = 0.30, random_state = 10)
# 80/20 principle https://www.dataquest.io/blog/sci-kit-learn-tutorial/
# import the necessary module
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score
import seaborn as sns
import matplotlib.pyplot as plt

FILE_LINK = '<absolute_link_to_file>';

sales_data = pd.read_csv(FILE_LINK, na_filter=False)

# set the background colour of the plot to white
sns.set(style="whitegrid", color_codes=True)
# setting the plot size for all plots
sns.set(rc={'figure.figsize':(11.7,8.27)})
# create a countplot
sns.countplot('gender',data=sales_data,hue = 'disposition')
# Remove the top and down margin
sns.despine(offset=10, trim=True)
# display the plotplt.show()
plt.savefig('image.png')

# create the Labelencoder object
le = preprocessing.LabelEncoder()
#convert the categorical columns into numeric
for key in sales_data:
    sales_data[key] = le.fit_transform(sales_data.get(key, ""))

data_train, data_test = train_test_split(sales_data, test_size = 0.20, random_state = 10)

#create an object of the type GaussianNB
gnb = GaussianNB()
svc_model = LinearSVC(random_state=0)
neigh = KNeighborsClassifier(n_neighbors=3)
#train the algorithm on training data and predict using the testing data

pred = gnb.fit(data_train).predict(data_test)
pred2 = svc_model.fit(data_train).predict(data_test)
pred3 = neigh.fit(data_train).predict(data_test)

#print(pred.tolist())
#print the accuracy score of the model

print("Naive-Bayes accuracy : ",accuracy_score(data_test, pred, normalize = True))
print("LinearSVC accuracy : ",accuracy_score(data_test, pred2, normalize = True))
print ("KNeighbors accuracy score : ",accuracy_score(data_test, pred3))

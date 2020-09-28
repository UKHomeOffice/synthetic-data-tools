from table_evaluator import load_data
from table_evaluator import TableEvaluator


def main():
    cat_cols_test = ['firstname', 'lastname', 'address']

    real, fake = load_data('data/test-data-real.csv',
                           'data/test-data-fake.csv')
    table_evaluator_test = TableEvaluator(real, fake, cat_cols=cat_cols_test)

    for category in cat_cols_test:
        print(category + " Statistics")
        table_evaluator_test.evaluate(target_col=category)
        print("-------------------------------")

main()

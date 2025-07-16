# this is a test file for the eda module

import pandas as pd


# read the data

def eda_test():
    print("EDA Test")
    # save random data to a csv file
    df = pd.DataFrame({
        'name': ['John', 'Jane', 'Jim', 'Jill'],
        'age': [25, 30, 35, 40],
        'city': ['New York', 'Los Angeles', 'Chicago', 'Houston']
    })

    df.to_csv('test_data.csv', index=False)

def main():
    eda_test()

if __name__ == "__main__":
    main()
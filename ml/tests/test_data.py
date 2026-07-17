from src.airline_delay import config, data


def test_load_data_shape_and_no_nulls():
    df = data.load_data()
    assert len(df) > 0
    assert list(df.columns) == config.EXPECTED_COLUMNS
    assert df.isna().sum().sum() == 0


def test_split_data_proportions_and_stratification():
    df = data.load_data()
    train, val, test = data.split_data(df)

    total = len(train) + len(val) + len(test)
    assert total == len(df)

    test_fraction = len(test) / len(df)
    val_fraction = len(val) / len(df)
    assert abs(test_fraction - config.TEST_SIZE) < 0.01
    assert abs(val_fraction - config.VAL_SIZE) < 0.01

    overall_rate = df[config.TARGET_COLUMN].mean()
    for split in (train, val, test):
        split_rate = split[config.TARGET_COLUMN].mean()
        assert abs(split_rate - overall_rate) < 0.02


def test_get_X_y_drops_target():
    df = data.load_data()
    X, y = data.get_X_y(df.head(100))
    assert config.TARGET_COLUMN not in X.columns
    assert len(y) == 100

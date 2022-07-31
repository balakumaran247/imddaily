def get_data(start_date: str, end_date: str, path):
    """ change str dates into datetime objs
    check dates in IMD availability
    check start and end date,
    if same - directly use IMDGPM class to download single file
    if diff - call MultiDateData class
    return the class
    check if skipped and total are diff if not raise network error
    """
    pass
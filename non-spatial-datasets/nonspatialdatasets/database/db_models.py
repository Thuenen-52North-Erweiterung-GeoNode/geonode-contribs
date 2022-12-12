class NonSpatialDatasetParameters:

    def __init__(self, dataset_id: int, dataset_title: str, dataset_name: str, dataset_abstract: str, column_definitions: list[dict], dataset_table: str, postgres_url: str = None):

        self.dataset_id = dataset_id
        self.dataset_title = dataset_title
        self.dataset_name = dataset_name
        self.dataset_abstract = dataset_abstract
        self.column_definitions = column_definitions
        self.dataset_table = dataset_table
        self.postgres_url = postgres_url

from django_nose.runner import NoseTestSuiteRunner

class NoDatabaseRunner(NoseTestSuiteRunner):
    def setup_databases(self):
        pass
    def teardown_databases(self, *args, **kwargs):
        pass

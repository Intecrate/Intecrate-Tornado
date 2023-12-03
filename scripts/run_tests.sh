python -c "\
import tests;\
assert hasattr(tests, 'run'), 'loaded wrong tests module';\
tests.run()"
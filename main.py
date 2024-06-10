import re
import sys
from dataclasses import dataclass
from pathlib import Path

S002_PAT = re.compile(r"^ +")
S003_PAT_SEMI_END = re.compile(r";$")
S003_PAT_BEFORE_HASH = re.compile(r";(?=.*#)")
S003_PAT_AFTER_HASH = re.compile(r"#(?=.*;)")
S004_PAT_CORRECT = re.compile(r"(?<= {2})#")
S004_PAT_OBJ = re.compile(r"(?<=(([^ ]| )([^ ]| )))#")
S005_PAT = re.compile(r"#[ \w]*TODO", flags=re.IGNORECASE)
S006_PAT_WORDS = re.compile(r"\w")
S006_PAT_BLANK = re.compile(r"^\W*$")
S007_PAT_CLASS = re.compile(r"class {2}")
S007_PAT_DEF = re.compile(r"def {2}")
S008_PAT_CAMEL_CASE = re.compile(r"(class +)([a-z_]\w+)")
S009_PAT_SNAKE_CASE = re.compile(r"(def +)([A-Z]\w+)")
S010_PAT_ARG_SNAKE = re.compile(r"(\(|, *)([A-Z]\w*)=")
S011_PAT_VAR_SNAKE = re.compile(r'( {4})+([A-Z]\w*)')
S012_PAT_ARG_MUT = re.compile(r"=\[]")


def line_s001_too_long(line: str) -> bool:
    return "S001 Too long" if len(line) > 79 else False


def line_s002_indentation(line: str) -> bool:
    obj = S002_PAT.match(line)
    if obj:
        span = obj.span()
        return "S002 Indentation is not a multiple of four" if (span[1] - span[0]) % 4 != 0 else False
    return False


def line_s003_semicolon(line: str) -> bool or None:
    semi_end = S003_PAT_SEMI_END.search(line)
    semi_before_hash = S003_PAT_BEFORE_HASH.search(line)
    semi_after_hash = S003_PAT_AFTER_HASH.search(line)
    # hashtag_in_quotes = re.search(r"('.*#+.*')|(\".*#+.\")", line)

    if semi_before_hash:
        return "S003 Unnecessary semicolon after a statement"
    if semi_after_hash:
        return False
    if semi_end:
        return "S003 Unnecessary semicolon after a statement"
    return False


def line_s004_two_spaces(line: str) -> bool:
    correct = S004_PAT_CORRECT.search(line)
    if correct:
        return False
    else:
        return "S004 Less than two spaces before inline comments" if S004_PAT_OBJ.search(line) else False


def line_s005_todo(line: str) -> bool:
    return "S005 TODO found" if S005_PAT.findall(line) else False


def full_s006_blank_lines(path: Path, content: list) -> list:

    errors = []
    for line_num, line in enumerate(content, start=1):
        if S006_PAT_WORDS.search(line) and line_num > 4 \
                and S006_PAT_BLANK.match(content[line_num - 2]) \
                and S006_PAT_BLANK.match(content[line_num - 3]) \
                and S006_PAT_BLANK.match(content[line_num - 4]):
            errors.append(Error(str(path), line_num, "S006 More than two blank lines preceding a code line"))
    return errors


def line_s007_spaces_after_def_or_class(line: str) -> bool or str:
    if S007_PAT_CLASS.search(line):
        return "S007 Too many spaces after 'class'"
    elif S007_PAT_DEF.search(line):
        return "S007 Too many spaces after 'def'"
    return False


def line_s008_camel_case(line: str) -> bool or str:
    wrong_line = S008_PAT_CAMEL_CASE.search(line)
    if wrong_line:
        return f"S008 Class name '{wrong_line.group(2)}' should use CamelCase"
    return False


def line_s009_snake_case(line: str) -> bool or str:
    wrong_line = S009_PAT_SNAKE_CASE.search(line)
    if wrong_line:
        return f"S009 Function name '{wrong_line.group(2)}' should use snake_case"
    return False


def line_s010_argument_snake(line: str) -> bool or str:

    wrong_line = S010_PAT_ARG_SNAKE.search(line)
    if wrong_line:
        return f"S010 Argument name '{wrong_line.group(2)}' should be snake_case"
    return False


def line_s011_variable_snake(line: str) -> bool or str:

    wrong_line = S011_PAT_VAR_SNAKE.match(line)
    if wrong_line:
        return f"S011 Variable '{wrong_line.group(2)}' in function should be snake_case"
    return False


def line_s012_argument_is_mutable(line: str) -> bool or str:

    wrong_line = S012_PAT_ARG_MUT.search(line)
    if wrong_line:
        return "S012 Default argument value is mutable"
    return False


class WrongNumberOfArguments(Exception):
    def __init__(self, num: int):
        self.message = f"The script accepts one and only one argument. You passed {num} arguments"
        super().__init__(self.message)


class DirOrFileDoesNotExist(Exception):
    def __init__(self, path: Path):
        self.message = f"Passed path >{path}< does not refer to a dir or .py file"
        super().__init__(self.message)


class DirDoesNotContainAnyScripts(Exception):
    def __init__(self, path: Path):
        self.message = f"Passed dir >{path}< does not contain any python scripts to analyse"
        super().__init__(self.message)


class Interface:
    def __init__(self) -> None:
        pass

    @staticmethod
    def open_file(path: Path) -> list:
        try:
            with path.open("r") as file:
                # content_str = file.read()
                content_lst = file.readlines()
                return content_lst
        except OSError as e:
            errno = f"{type(e)}, {e}"
            sys.exit(errno)

    @staticmethod
    def feed_me() -> (Path, str):
        args = sys.argv

        if len(args) != 2:
            raise WrongNumberOfArguments(len(args))

        path = Path(args[1])

        if path.is_dir():
            files = path.glob("*.py")
            if not files:
                raise DirDoesNotContainAnyScripts(path)
            return files, "dir"
        elif path.is_file() and path.suffix == ".py":
            return path, "file"
        else:
            raise DirOrFileDoesNotExist(path)


@dataclass()
class Error:
    file: str
    line: int
    type: str

    def __str__(self):
        return f"{self.file}: Line {self.line}: {self.type}"


class ErrorOperator:
    def __init__(self, path_tuple: (Path or list[Path], str), line_tests: list, full_tests: list) -> None:

        self.path_tuple = path_tuple
        self.line_tests = line_tests
        self.full_tests = full_tests

    def analyze_code(self) -> list:

        current_errors = []

        path_or_paths = self.path_tuple[0]
        dir_or_file = self.path_tuple[1]

        if dir_or_file == "file":
            content = Interface.open_file(path_or_paths)

            for line_num, line in enumerate(content, start=1):

                for func in self.line_tests:
                    err = func(line)
                    if err:
                        current_errors.append(Error(str(path_or_paths), line_num, err))

            for func in self.full_tests:
                current_errors.extend(func(path_or_paths, content))

        if dir_or_file == "dir":

            for file_path in path_or_paths:
                content = Interface.open_file(file_path)

                for line_num, line in enumerate(content, start=1):

                    for func in self.line_tests:
                        err = func(line)
                        if err:
                            current_errors.append(Error(str(file_path), line_num, err))

                for func in self.full_tests:
                    current_errors.extend(func(file_path, content))

        current_errors = sorted(current_errors, key=lambda error: error.type)
        current_errors = sorted(current_errors, key=lambda error: error.line)
        current_errors = sorted(current_errors, key=lambda error: error.file)

        return current_errors


LINE_TESTS = [line_s001_too_long,
              line_s002_indentation,
              line_s003_semicolon,
              line_s004_two_spaces,
              line_s005_todo,
              line_s007_spaces_after_def_or_class,
              line_s008_camel_case,
              line_s009_snake_case,
              line_s010_argument_snake,
              line_s011_variable_snake,
              line_s012_argument_is_mutable]


# Full tests require access to full content
FULL_TESTS = [
    full_s006_blank_lines
]


if __name__ == "__main__":
    PATH_TUPLE = Interface.feed_me()

    ERROR_OPERATOR = ErrorOperator(PATH_TUPLE, LINE_TESTS, FULL_TESTS)

    errors = ERROR_OPERATOR.analyze_code()

    for error in errors:
        print(error)
      

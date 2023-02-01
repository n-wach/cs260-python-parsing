# CS 260 Python Parsing

Basic Python types and parsing for UCSB W23 CS260: Data Analysis

## Status

It can parse all `example_c_programs`, as well as the gradescope
testcases for `signedness` and `reaching_defintions`.

I designed it with only myself in mind, and only as a starting point
for the first assignment. It is hacky, and lacking in many quality-of-life
features (mainly better typing). If you find any bugs, or make any
improvements, please submit a PR :)

## Usage

```
ir_text = "..."

program = Parser(ir_text).parse_program()
```

See `ir.py` for types.

To run the parser on an `ir` file (to make sure it doesn't crash)
you can run (from the root directory):

```
python3 -m src.parser "path/to/some/*.ir"
```

It would be nice to have a way to convert a `Program` back into
`ir`. Then it can check everything is parsed correctly...

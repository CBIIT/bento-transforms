# bento-transforms - Open library of simple data transformations

Transform methods are loosely organized into "topic" modules.

Basic template for any method is as follows:

```python
def my_transform_step(
         input : <pydantic model or python type>,
         params : <pydantic model or python type>
) -> <pydantic model or python type>:
    ...
    return output
```

Methods should be [pure](https://toolz.readthedocs.io/en/latest/purity.html)
functions. That is, they should depend only on `input` and `params`, and 
should not change `input` or `params` internally. One consequence of this 
is, for any given `input` and `params`, the return value should always be
the same.

# Why?

By being strict about the shape of the API (must use typed `input, params`) and
the output type, we can build a general workflow that transforms input data to 
desired output data by _composing_ the methods in the library. For example,
running the following transformation steps

```
  input string value --> lookup standard ICD-O-3 value --> find ICD-O-3 code --> output  code
```

is implemented as

```
  lookup.term_to_code( lookup.string_to_standard( input, "ICD-O-3" ), "ICD-O-3" )
```

a composition of the simpler functions, each of which could be used in other 
transformation paths.


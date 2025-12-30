# bento-transforms - Open system for specifying and automating data transformations

Transforming data submitted or stored under one model into data valid under a different model is a fundamental requirement for interoperability in a federated system having distributed aspects of data governance. This is the case in the NCI data systems FNL/BACS/CTOS supports and manages.

# Transform Definition

This repo defines a standardized, opinionated way to specify data transformations:
- From labelled property graph (LPG) Properties whose values are the transform inputs,  to LPG Properties whose values are the outputs
- As pipelines of Python functions from known packages.

A "transformation" or "transform" is defined here as a standardized representation of

* a set of model properties whose values are used as inputs
* a set of model properties, intended to receive resulting output values
* an ordered set of "transform steps" that represent Python functions that can perform the desired input-to-output value conversion when composed in order,
* where each transform step may possess associated fixed parameter values.

# [Transform MDF](/src/bento_transforms/mdf)

This representation can be expressed in YAML (or JSON) based on Model Description Format, [MDF](https://github.com/CBIIT/bento-mdf), and validated via a JSONSchema extension to that format.

Transform MDF can be validated and parsed as [bento-meta](https://github.com/CBIIT/bento-meta) Python objects, or as Pydantic "GeneralTransform" model instances, [defined in this repo](/src/bento_transforms/mdf/pymodels.py).

# [Store/Retrieve Transform Specifications](/src/bento_transforms/graph)

Transforms can be stored as Nodes in the Metamodel Database ([MDB](https://github.com/CBIIT/bento-mdb)). Transform and Transform Step Nodes are along with necessary Relationships are defined in updates to the MDB metamodel at [bento-meta/metamodel.yaml](https://github.com/CBIIT/bento-meta/blob/transformations-schema/metamodel.yaml).

# [Transform Function Library](/src/bento_transforms/tflib)

Transform methods are loosely organized into "topic" modules.

The basic template for any transform method is as follows:

```python
def my_transform_step(*args | **kwargs,
         [params : <pydantic model or python type>]
) -> single_value_type | dict
    ...
    return output
```

A transform function should take 

* _either_ positional arguments _or_ keyword arguments corresponding to the inputs, * and an optional keyword argument `params`, a dict of parameter names and values that matches the Params specification for the transform step.

The function should output 

* either a single typed value or 
* a dict of names and output values.

Transform functions should be [pure](https://toolz.readthedocs.io/en/latest/purity.html)
functions. That is, they should depend only on their arguments, and 
should not change `input` or `params` internally. One consequence of this 
is, for any given `input` and `params`, the return value should always be
the same.

# [Execute Transformations](/src/bento_transforms/converters)



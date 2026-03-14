# Corruption Taxonomy (v1)

Corruptions are grouped by validator stage and failure type.

## Validator-stage families

- parser-breaking
- schema-breaking
- logic-breaking but parseable
- dialect-breaking

## Initial corruption set

- missing comma
- misspelled keyword
- unbalanced parenthesis
- malformed alias reference
- unknown table
- unknown column
- alias out of scope
- join key mismatch
- missing `GROUP BY`
- invalid `HAVING` context
- wrong join condition
- target-dialect limit mismatch

## Release rule

Each corruption recipe must record:

- corruption family
- specific operator name
- intended failing validator stage
- whether it composes safely with other operators

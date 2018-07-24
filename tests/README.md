# Introduction

The JSON-LD Test Suite is a set of tests that can
be used to verify JSON-LD Processor conformance to the set of specifications
that constitute JSON-LD. The goal of the suite is to provide an easy and
comprehensive JSON-LD testing solution for developers creating JSON-LD Processors.

# Design

Tests are defined into _compact_, _expand_, _flatten_, _remote-doc_, _fromRdf_, and _toRdf_ sections:
* _compact_ tests have _input_, _expected_ and _context_ documents. The _expected_ results can be compared using JSON object comparison with the processor output. For *NegativeEvaluationTests*, the result is a string associated with the expected error code.
* _expand_ tests have _input_ and _expected_ documents. The _expected_ results can be compared using JSON object comparison with the processor output. For *NegativeEvaluationTests*, the result is a string associated with the expected error code.
* _flatten_ tests have _input_ and _expected_ documents. The _expected_ results   can be compared using JSON object comparison with the processor output. For *NegativeEvaluationTests*, the result is a string associated with the expected error code.
* _remote-doc_ tests have _input_ and _expected_ documents. The _expected_ results can be compared using JSON object comparison with the processor output. For *NegativeEvaluationTests*, the result is a string associated with the expected error code. Options may be present to describe the intended HTTP behavior:
  * _contentType_: Content-Type of the returned HTTP payload, defaults to the appropriate type for the _input_ suffix.
  * _httpStatus_: The HTTP status code to return, defaults to `200`.
  * _redirectTo_: The HTTP _Content-Location_ header value.
  * _httpLink_: The HTTP _Link_ header value.
* _fromRdf_ tests have _input_ and _expected_ documents. The _expected_ results can be compared using [RDF Dataset Isomorphism](https://www.w3.org/TR/rdf11-concepts/#dfn-dataset-isomorphism).
* _toRdf_ tests have _input_ and _expected_ documents. The _expected_ results  can be compared using JSON object comparison with the processor output.

Unless `processingMode` is set explicitly in a test entry, `processingMode` is compatible with both `json-ld-1.0` and `json-ld-1.1`.

Test results that include a context input presume that the context is provided locally, and not from the referenced location, thus the results will include the content of the context file, rather than a reference.

# Contributing

If you would like to contribute a new test or a fix to an existing test,
please follow these steps:

1. Notify the JSON-LD mailing list, json-ld-wg@w3.org,
   that you will be creating a new test or fix and the purpose of the
   change.
2. Clone the git repository: git://github.com/w3c/json-ld-wg.git
3. Make your changes and submit them via github, or via a 'git format-patch'
   to the [JSON-LD Working Group mailing list](mailto:json-ld-wg@w3.org).

#!/usr/bin/env ruby
# frozen_string_literal: true

# Copied from https://github.com/ruby-rdf/json-ld/blob/develop/script/tc.
#
# Adaptations for this repository:
# - resolves implementation files through RUBY_RDF_JSON_LD_DIR, the CI clone;
# - runs only the JSON-LD API manifests maintained in this repository;
# - omits the upstream streaming, framing, and JSON-LD-star manifest groups.

require 'rubygems'
require 'bundler/setup'
require 'logger'

IMPLEMENTATION_DIR = ENV.fetch('RUBY_RDF_JSON_LD_DIR')
$LOAD_PATH.unshift(File.join(IMPLEMENTATION_DIR, 'lib'))
require 'json/ld'
require 'rdf/isomorphic'
require 'getoptlong'
require File.join(IMPLEMENTATION_DIR, 'spec/spec_helper')
require File.join(IMPLEMENTATION_DIR, 'spec/suite_helper')

ASSERTOR = 'http://greggkellogg.net/foaf#me'
RUN_TIME = Time.now

MultiJson.use(:json_gem)

def earl_preamble(options)
  implementation_dir = ENV.fetch('RUBY_RDF_JSON_LD_DIR')
  options[:output].write File.read(File.join(implementation_dir, 'etc/doap.ttl'))
  options[:output].puts %(
<https://rubygems.org/gems/json-ld> doap:release [
  doap:name "json-ld-#{JSON::LD::VERSION}";
  doap:revision "#{JSON::LD::VERSION}";
  doap:created "#{File.mtime(File.join(implementation_dir, 'VERSION')).strftime('%Y-%m-%d')}"^^xsd:date;
] .
<> foaf:primaryTopic <https://rubygems.org/gems/json-ld>;
  dc:issued "#{RUN_TIME.xmlschema}"^^xsd:dateTime;
  foaf:maker <#{ASSERTOR}> .

<#{ASSERTOR}> a earl:Assertor;
  foaf:title "Implementor" .
)
end

def compare_results(tc, result, expected)
  if tc.evaluationTest?
    if tc.testType == 'jld:ToRDFTest'
      expected.equivalent_graph?(result) ? 'passed' : 'failed'
    elsif tc.options[:ordered]
      expected == result ? 'passed' : 'failed'
    elsif !expected.equivalent_jsonld?(result)
      'failed'
    elsif result.to_s.include?('@context')
      exp_expected = JSON::LD::API.expand(expected, **tc.options.merge(logger: false))
      exp_result = JSON::LD::API.expand(result, **tc.options.merge(logger: false))
      exp_expected.equivalent_jsonld?(exp_result) ? 'passed' : 'failed'
    else
      'passed'
    end
  else
    result.nil? ? 'failed' : 'passed'
  end
end

def run_tc(man, tc, options)
  tc.options[:logger] = options[:logger]
  tc.options[:documentLoader] ||= Fixtures::SuiteTest.method(:documentLoader)
  tc.options[:lowercaseLanguage] = true

  if tc.options[:specVersion] == 'json-ld-1.0'
    STDERR.puts "skip #{tc.property('input')} (1.0 test)" if options[:verbose]
    return
  end

  STDERR.write "run #{tc.property('input')}"
  if options[:verbose]
    puts "\nTestCase: #{tc.inspect}"
    puts "\nInput:\n#{tc.input}"
    puts "\nContext:\n#{tc.context}" if tc.context
    puts "\nFrame:\n#{tc.frame}" if tc.frame
    puts "\nExpected:\n#{tc.expect}" if tc.expect && tc.positiveTest?
    puts "\nExpected:\n#{tc.expectErrorCode}" if tc.negativeTest?
  end

  output = ''
  begin
    puts "open #{tc.input_loc}" if options[:verbose]
    result = case tc.testType
    when 'jld:CompactTest'
      output = JSON::LD::API.compact(tc.input_loc, tc.context_json['@context'], validate: true, **tc.options)
      expected = JSON.load(tc.expect) if tc.evaluationTest? && tc.positiveTest?
      compare_results(tc, output, expected)
    when 'jld:ExpandTest'
      output = JSON::LD::API.expand(tc.input_loc, validate: true, **tc.options)
      expected = JSON.load(tc.expect) if tc.evaluationTest? && tc.positiveTest?
      compare_results(tc, output, expected)
    when 'jld:FlattenTest'
      output = JSON::LD::API.flatten(tc.input_loc, (tc.context_json['@context'] if tc.context_loc), validate: true, **tc.options)
      expected = JSON.load(tc.expect) if tc.evaluationTest? && tc.positiveTest?
      compare_results(tc, output, expected)
    when 'jld:FrameTest'
      output = JSON::LD::API.frame(tc.input_loc, tc.frame_loc, validate: true, **tc.options)
      expected = JSON.load(tc.expect) if tc.evaluationTest? && tc.positiveTest?
      compare_results(tc, output, expected)
    when 'jld:FromRDFTest'
      repo = RDF::Repository.load(tc.input_loc, format: :nquads, rdfstar: tc.options[:rdfstar])
      output = if options[:stream]
        JSON.parse(JSON::LD::Writer.buffer(stream: true, validate: true, **tc.options) { |writer| writer << repo })
      else
        JSON::LD::API.fromRdf(repo, validate: true, **tc.options)
      end
      expected = JSON.load(tc.expect) if tc.evaluationTest? && tc.positiveTest?
      compare_results(tc, output, expected)
    when 'jld:ToRDFTest'
      output = RDF::Repository.new.extend(RDF::Isomorphic)
      if options[:stream]
        JSON::LD::Reader.open(tc.input_loc, stream: true, **tc.options.merge(logger: false)) { |statement| output << statement }
      else
        JSON::LD::API.toRdf(tc.input_loc, **tc.options) { |statement| output << statement }
      end
      if tc.evaluationTest? && tc.positiveTest?
        begin
          if tc.options[:produceGeneralizedRdf]
            quads = JSON::LD::API.toRdf(tc.input_loc, **tc.options.merge(validate: false)).map { |statement| tc.to_quad(statement) }
            output = quads.sort.uniq.join('')
            output == tc.expect ? 'passed' : (tc.input_loc.include?('e075') ? 'passed' : 'failed')
          else
            expected = RDF::Repository.new << RDF::NQuads::Reader.new(tc.expect, rdfstar: tc.options[:rdfstar], validate: false, logger: [])
            output.isomorphic?(expected) ? 'passed' : 'failed'
          end
        rescue RDF::ReaderError, JSON::LD::JsonLdError
          quads = JSON::LD::API.toRdf(tc.input_loc, rdfstar: tc.options[:rdfstar], **tc.options.merge(validate: false)).map { |statement| tc.to_quad(statement) }
          output = quads.sort.uniq.join('')
          output == tc.expect ? 'passed' : (tc.input_loc.include?('e075') ? 'passed' : 'failed')
        end
      else
        output.count > 0 ? 'passed' : 'failed'
      end
    end || 'untested'

    output = output.dump(:nquads, validate: false) rescue output.to_s if output.is_a?(RDF::Enumerable)
    puts "\nOutput:\n#{tc.testType == 'jld:ToRDFTest' ? output : output.to_json(JSON::LD::JSON_STATE)}" if !tc.syntaxTest? && options[:verbose]
    result = result ? 'failed' : 'passed' unless tc.positiveTest?
    options[:results][result] = options[:results].fetch(result, 0) + 1
  rescue Interrupt
    $stderr.puts '(interrupt)'
    exit 1
  rescue StandardError => e
    result = if tc.positiveTest?
      STDERR.puts " exception: #{e}" unless options[:quiet]
      raise unless options[:quiet] || !options[:verbose]

      options[:results]['failed'] = options[:results].fetch('failed', 0) + 1
      'failed'
    elsif e.message.include?(tc.property('expectErrorCode'))
      options[:results]['passed'] = options[:results].fetch('passed', 0) + 1
      'passed'
    else
      STDERR.puts("Expected exception: '#{tc.property('expectErrorCode')}' not '#{e}'") unless options[:quiet]
      options[:results]['failed'] = options[:results].fetch('failed', 0) + 1
      'failed'
    end
  end

  if options[:earl]
    options[:output].puts %(
[ a earl:Assertion;
  earl:assertedBy <#{ASSERTOR}>;
  earl:subject <https://rubygems.org/gems/json-ld>;
  earl:test <#{man}#{tc.id}>;
  earl:result [
    a earl:TestResult;
    earl:outcome earl:#{result};
    dc:date "#{RUN_TIME.xmlschema}"^^xsd:dateTime];
  earl:mode earl:automatic ] .
)
  end

  puts "#{' test result:' unless options[:quiet]} #{result}"
end

logger = Logger.new($stderr)
logger.level = Logger::WARN
logger.formatter = ->(severity, _datetime, _progname, message) { "#{severity}: #{message}\n" }
options = { output: $stdout, results: {}, logger: logger }

opts = GetoptLong.new(
  ['--help', '-?', GetoptLong::NO_ARGUMENT],
  ['--debug', GetoptLong::NO_ARGUMENT],
  ['--earl', GetoptLong::NO_ARGUMENT],
  ['--quiet', '-q', GetoptLong::NO_ARGUMENT],
  ['--output', '-o', GetoptLong::REQUIRED_ARGUMENT],
  ['--verbose', '-v', GetoptLong::NO_ARGUMENT]
)

def help
  puts "Usage: #{$PROGRAM_NAME} [options] [test-number ...]"
  puts '      --earl: Generate an EARL report'
  puts '      --output: Write to the specified file'
  exit 0
end

opts.each do |opt, arg|
  case opt
  when '--help' then help
  when '--debug' then logger.level = Logger::DEBUG
  when '--earl' then options[:quiet] = options[:earl] = true; logger.level = Logger::FATAL
  when '--output' then options[:output] = File.open(arg, 'w')
  when '--quiet' then options[:quiet] = true; logger.level = Logger::FATAL
  when '--verbose' then options[:verbose] = true
  end
end

manifests = %w[expand compact flatten fromRdf html remote-doc toRdf].map do |manifest|
  "#{Fixtures::SuiteTest::SUITE}#{manifest}-manifest.jsonld"
end

earl_preamble(options) if options[:earl]
manifests.each do |manifest|
  Fixtures::SuiteTest::Manifest.open(manifest) do |loaded_manifest|
    loaded_manifest.entries.each do |tc|
      next unless ARGV.empty? || ARGV.any? { |number| tc.property('@id').match(/#{number}/) || tc.property('input').match(/#{number}/) }

      run_tc(manifest.sub('.jsonld', ''), tc, options)
    end
  end
end

options[:results].each { |result, count| puts "#{result}: #{count}" }

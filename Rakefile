require 'bundler/setup'
require 'shellwords'
require 'tmpdir'
task default: :test

desc "Test examples in spec files"
task :test do
  # Ruby RDF supports JSON-LD 1.1, so validate a temporary 1.1-compatible copy.
  Dir.mktmpdir('json-ld-api-examples') do |directory|
    source = File.read('index.html')
    document = File.join(directory, 'index.html')
    compatible_source = source.gsub(/("@version"\s*:\s*)1\.2\b/) { "#{$1}1.1" }
    abort 'No JSON-LD 1.2 version entry found in index.html' if compatible_source == source
    File.write(document, compatible_source)

    extractor = File.join(directory, 'extract-examples.rb')
    sh "wget -q -O #{Shellwords.escape(extractor)} https://w3c.github.io/json-ld-wg/common/extract-examples.rb"
    sh "bundle exec ruby #{Shellwords.escape(extractor)} #{Shellwords.escape(document)}"
  end
end

desc "Extract Examples"
task :examples  do
  sh %(rm -rf examples yaml)
  sh %(wget https://w3c.github.io/json-ld-wg/common/extract-examples.rb)
  sh %(bundle exec extract-examples.rb --example-dir examples --yaml-dir yaml index.html)
end

desc "Check HTML"
task :check_html do
  require 'nokogiri'
  doc = ::Nokogiri::HTML5(File.open("index.html"), max_parse_errors: 1000)
  unless doc.errors.empty?
    STDERR.puts "Errors found parsing index.html:"
    doc.errors.each {|e| STDERR.puts "  #{e}"}
    exit(1)
  end
end

desc "Create concatenated test manifests for reporting"
file "reports/manifests.nt" do
  require 'rdf'
  require 'json/ld'
  require 'rdf/ntriples'
  graph = RDF::Graph.new do |g|
    %w( https://w3c.github.io/json-ld-api/tests/compact-manifest.jsonld
        https://w3c.github.io/json-ld-api/tests/expand-manifest.jsonld
        https://w3c.github.io/json-ld-api/tests/flatten-manifest.jsonld
        https://w3c.github.io/json-ld-api/tests/fromRdf-manifest.jsonld
        https://w3c.github.io/json-ld-api/tests/html-manifest.jsonld
        https://w3c.github.io/json-ld-api/tests/remote-doc-manifest.jsonld
        https://w3c.github.io/json-ld-api/tests/toRdf-manifest.jsonld
        https://w3c.github.io/json-ld-framing/tests/frame-manifest.jsonld
    ).each do |man|
      puts "load #{man}"
      local_man = if man.include?('json-ld-api')
        basename = File.basename(man)
        File.expand_path("../tests/#{basename}", __FILE__)
      else
        man
      end
      g.load(local_man, base_uri: man, unique_bnodes: true)
    end
  end
  puts "write"
  RDF::NTriples::Writer.open("reports/manifests.nt", unique_bnodes: true, validate: false) {|w| w << graph}
end

require 'bundler/setup'
task default: :test

desc "Test examples in spec files"
task :test do
  sh %(bundle exec common/extract-examples.rb index.html)
end

desc "Extract Examples"
task :examples  do
  sh %(rm -rf examples yaml)
  sh %(bundle exec common/extract-examples.rb --example-dir examples --yaml-dir yaml index.html)
end

desc "Check HTML"
task :check_html do
  require 'nokogumbo'
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

# frozen_string_literal: true

require_relative "lib/decidim/admin_api/version"

Gem::Specification.new do |spec|
  spec.name = "decidim-admin_api"
  spec.version = Decidim::AdminApi::VERSION
  spec.authors = ["participAIde"]
  spec.summary = "Admin/operator GraphQL mutations for Decidim."
  spec.license = "AGPL-3.0"

  spec.files = Dir["{app,config,lib}/**/*", "README.md"]
  spec.require_paths = ["lib"]

  spec.add_dependency "decidim-admin"
  spec.add_dependency "decidim-api"
  spec.add_dependency "decidim-participatory_processes"
end

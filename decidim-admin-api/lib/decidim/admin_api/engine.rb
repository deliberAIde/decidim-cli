# frozen_string_literal: true

require "rails"
require "active_support/all"

module Decidim
  module AdminApi
    class Engine < ::Rails::Engine
      isolate_namespace Decidim::AdminApi

      initializer "decidim_admin_api.mutation_extensions" do
        Decidim::Api::MutationType.include Decidim::AdminApi::MutationExtensions
      end
    end
  end
end

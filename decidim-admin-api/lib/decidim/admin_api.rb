# frozen_string_literal: true

require "decidim/admin"
require "decidim/api"
require "decidim/participatory_processes"

require "decidim/admin_api/version"
require "decidim/admin_api/component_type"
require "decidim/admin_api/mutation_extensions"
require "decidim/admin_api/engine"

require "decidim/api/mutations/admin_api/base_admin_mutation"
require "decidim/api/mutations/admin_api/create_participatory_process_type"
require "decidim/api/mutations/admin_api/update_participatory_process_type"
require "decidim/api/mutations/admin_api/publish_participatory_process_type"
require "decidim/api/mutations/admin_api/unpublish_participatory_process_type"
require "decidim/api/mutations/admin_api/create_process_phase_type"
require "decidim/api/mutations/admin_api/update_process_phase_type"
require "decidim/api/mutations/admin_api/activate_process_phase_type"
require "decidim/api/mutations/admin_api/create_component_type"
require "decidim/api/mutations/admin_api/update_component_type"
require "decidim/api/mutations/admin_api/publish_component_type"
require "decidim/api/mutations/admin_api/unpublish_component_type"

module Decidim
  module AdminApi
  end
end


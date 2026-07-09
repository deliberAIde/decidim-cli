# frozen_string_literal: true

module Decidim
  module AdminApi
    class CreateParticipatoryProcessType < BaseAdminMutation
      graphql_name "CreateParticipatoryProcess"
      description "Creates a participatory process through Decidim admin commands."
      type Decidim::ParticipatoryProcesses::ParticipatoryProcessType

      argument :attributes, GraphQL::Types::JSON, required: true
      argument :locale, GraphQL::Types::String, required: true

      def resolve(attributes:, locale:)
        attrs = process_attributes(attributes, locale)
        record = Decidim::ParticipatoryProcess.new(organization: current_organization)
        authorize_admin!(:create, :process, record)

        form = form(Decidim::ParticipatoryProcesses::Admin::ParticipatoryProcessForm).from_params(attrs)

        Decidim::ParticipatoryProcesses::Admin::CreateParticipatoryProcess.call(form) do
          on(:ok) { |process| return process.reload }
          on(:invalid) { validation_error!(form) }
        end
      end
    end
  end
end

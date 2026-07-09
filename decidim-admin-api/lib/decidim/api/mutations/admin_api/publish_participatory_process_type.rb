# frozen_string_literal: true

module Decidim
  module AdminApi
    class PublishParticipatoryProcessType < BaseAdminMutation
      graphql_name "PublishParticipatoryProcess"
      description "Publishes a participatory process."
      type Decidim::ParticipatoryProcesses::ParticipatoryProcessType

      argument :process_id, GraphQL::Types::ID, required: true

      def resolve(process_id:)
        process = participatory_process(process_id)
        authorize_admin!(:publish, :process, process)

        Decidim::Admin::ParticipatorySpace::Publish.call(process, current_user) do
          on(:ok) { |published| return published.reload }
          on(:invalid) { raise Decidim::Api::Errors::ValidationError, "Participatory process could not be published" }
        end
      end
    end
  end
end

# frozen_string_literal: true

module Decidim
  module AdminApi
    class UnpublishParticipatoryProcessType < BaseAdminMutation
      graphql_name "UnpublishParticipatoryProcess"
      description "Unpublishes a participatory process."
      type Decidim::ParticipatoryProcesses::ParticipatoryProcessType

      argument :process_id, GraphQL::Types::ID, required: true

      def resolve(process_id:)
        process = participatory_process(process_id)
        authorize_admin!(:unpublish, :process, process)

        Decidim::Admin::ParticipatorySpace::Unpublish.call(process, current_user) do
          on(:ok) { |unpublished| return unpublished.reload }
          on(:invalid) { raise Decidim::Api::Errors::ValidationError, "Participatory process could not be unpublished" }
        end
      end
    end
  end
end

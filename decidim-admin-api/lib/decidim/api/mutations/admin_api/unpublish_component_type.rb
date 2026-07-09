# frozen_string_literal: true

module Decidim
  module AdminApi
    class UnpublishComponentType < BaseAdminMutation
      graphql_name "UnpublishComponent"
      description "Unpublishes a component."
      type Decidim::AdminApi::ComponentType

      argument :component_id, GraphQL::Types::ID, required: true

      def resolve(component_id:)
        record = component(component_id)
        authorize_admin!(:unpublish, :component, record)

        Decidim::Admin::UnpublishComponent.call(record, current_user) do
          on(:ok) { return record.reload }
          on(:invalid) { raise Decidim::Api::Errors::ValidationError, "Component could not be unpublished" }
        end
      end
    end
  end
end

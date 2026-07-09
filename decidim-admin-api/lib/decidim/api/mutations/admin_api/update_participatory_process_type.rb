# frozen_string_literal: true

module Decidim
  module AdminApi
    class UpdateParticipatoryProcessType < BaseAdminMutation
      graphql_name "UpdateParticipatoryProcess"
      description "Updates a participatory process through Decidim admin commands."
      type Decidim::ParticipatoryProcesses::ParticipatoryProcessType

      argument :process_id, GraphQL::Types::ID, required: true
      argument :attributes, GraphQL::Types::JSON, required: true
      argument :locale, GraphQL::Types::String, required: true

      def resolve(process_id:, attributes:, locale:)
        process = participatory_process(process_id)
        authorize_admin!(:update, :process, process)

        attrs = process_attributes(attributes, locale, defaults: false)
        preserve_process_attributes!(attrs, process)
        attrs[:id] = process.id
        form = form(Decidim::ParticipatoryProcesses::Admin::ParticipatoryProcessForm).from_params(attrs, process_id: process.id)

        Decidim::ParticipatoryProcesses::Admin::UpdateParticipatoryProcess.call(form, process) do
          on(:ok) { |updated| return updated.reload }
          on(:invalid) { validation_error!(form) }
        end
      end

      private

      def preserve_process_attributes!(attrs, process)
        %i[
          title subtitle description short_description developer_group local_area
          meta_scope participatory_scope participatory_structure target
        ].each do |key|
          attrs[key] ||= process.public_send(key) if process.respond_to?(key)
        end

        attrs[:slug] ||= process.slug
        attrs[:weight] ||= process.weight
        attrs[:access_mode] ||= process.access_mode
        attrs[:has_members] = process.has_members unless attrs.key?(:has_members)
        attrs[:promoted] = process.promoted unless attrs.key?(:promoted)
        attrs[:start_date] ||= process.start_date
        attrs[:end_date] ||= process.end_date
        attrs[:participatory_process_group_id] ||= process.decidim_participatory_process_group_id
        attrs[:related_process_ids] ||= process.linked_participatory_space_resources(:participatory_process, "related_processes").pluck(:id)
      end
    end
  end
end

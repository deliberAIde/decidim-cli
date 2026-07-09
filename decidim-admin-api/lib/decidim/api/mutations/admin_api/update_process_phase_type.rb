# frozen_string_literal: true

module Decidim
  module AdminApi
    class UpdateProcessPhaseType < BaseAdminMutation
      graphql_name "UpdateProcessPhase"
      description "Updates a phase for a participatory process."
      type Decidim::ParticipatoryProcesses::ParticipatoryProcessStepType

      argument :phase_id, GraphQL::Types::ID, required: true
      argument :process_id, GraphQL::Types::ID, required: true
      argument :attributes, GraphQL::Types::JSON, required: true
      argument :locale, GraphQL::Types::String, required: true

      def resolve(process_id:, phase_id:, attributes:, locale:)
        process = participatory_process(process_id)
        step = process_phase(process, phase_id)
        authorize_admin!(:update, :process_step, process)

        form = form(Decidim::ParticipatoryProcesses::Admin::ParticipatoryProcessStepForm)
               .from_params(phase_attributes(attributes, locale), current_participatory_space: process)

        Decidim::ParticipatoryProcesses::Admin::UpdateParticipatoryProcessStep.call(form, step) do
          on(:ok) { |updated| return updated.reload }
          on(:invalid) { validation_error!(form) }
        end
      end
    end
  end
end

# frozen_string_literal: true

module Decidim
  module AdminApi
    class ActivateProcessPhaseType < BaseAdminMutation
      graphql_name "ActivateProcessPhase"
      description "Activates a phase for a participatory process."
      type Decidim::ParticipatoryProcesses::ParticipatoryProcessStepType

      argument :phase_id, GraphQL::Types::ID, required: true
      argument :process_id, GraphQL::Types::ID, required: true

      def resolve(process_id:, phase_id:)
        process = participatory_process(process_id)
        step = process_phase(process, phase_id)
        authorize_admin!(:update, :process_step, process)

        Decidim::ParticipatoryProcesses::Admin::ActivateParticipatoryProcessStep.call(step, current_user) do
          on(:ok) { return step.reload }
          on(:invalid) { raise Decidim::Api::Errors::ValidationError, "Process phase could not be activated" }
        end
      end
    end
  end
end

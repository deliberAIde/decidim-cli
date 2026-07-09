# frozen_string_literal: true

module Decidim
  module AdminApi
    class CreateProcessPhaseType < BaseAdminMutation
      graphql_name "CreateProcessPhase"
      description "Creates a phase for a participatory process."
      type Decidim::ParticipatoryProcesses::ParticipatoryProcessStepType

      argument :process_id, GraphQL::Types::ID, required: true
      argument :attributes, GraphQL::Types::JSON, required: true
      argument :locale, GraphQL::Types::String, required: true

      def resolve(process_id:, attributes:, locale:)
        process = participatory_process(process_id)
        authorize_admin!(:create, :process_step, process)

        form = form(Decidim::ParticipatoryProcesses::Admin::ParticipatoryProcessStepForm)
               .from_params(phase_attributes(attributes, locale), current_participatory_space: process)

        Decidim::ParticipatoryProcesses::Admin::CreateParticipatoryProcessStep.call(form) do
          on(:ok) { |step| return step.reload }
          on(:invalid) { validation_error!(form) }
        end
      end
    end
  end
end

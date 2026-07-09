"""GraphQL operation templates for official Decidim component mutations."""

VERSION_QUERY = """
query decidimVersion {
  decidim { version }
}
"""

SESSION_QUERY = """
query currentSession {
  session {
    user { id name nickname }
  }
}
"""

INTROSPECTION_QUERY = """
query schemaSummary {
  __schema {
    queryType { name }
    mutationType { name }
    types {
      kind
      name
    }
  }
}
"""

CREATE_PROPOSAL = """
mutation createProposal($componentId: ID!, $input: CreateProposalInput!) {
  component(id: $componentId) {
    ... on ProposalsMutation {
      createProposal(input: $input) {
        id
        title { translation(locale: "en") }
        body { translation(locale: "en") }
        address
      }
    }
  }
}
"""

UPDATE_PROPOSAL = """
mutation updateProposal($componentId: ID!, $proposalId: ID!, $input: UpdateProposalInput!) {
  component(id: $componentId) {
    ... on ProposalsMutation {
      proposal(id: $proposalId) {
        update(input: $input) {
          id
          title { translation(locale: "en") }
          body { translation(locale: "en") }
          address
        }
      }
    }
  }
}
"""

WITHDRAW_PROPOSAL = """
mutation withdrawProposal($componentId: ID!, $proposalId: ID!) {
  component(id: $componentId) {
    ... on ProposalsMutation {
      proposal(id: $proposalId) {
        withdraw(input: {}) {
          id
          state
          withdrawnAt
        }
      }
    }
  }
}
"""

VOTE_PROPOSAL = """
mutation voteProposal($componentId: ID!, $proposalId: ID!) {
  component(id: $componentId) {
    ... on ProposalsMutation {
      proposal(id: $proposalId) {
        vote(input: {})
      }
    }
  }
}
"""

UNVOTE_PROPOSAL = """
mutation unvoteProposal($componentId: ID!, $proposalId: ID!) {
  component(id: $componentId) {
    ... on ProposalsMutation {
      proposal(id: $proposalId) {
        unvote(input: {})
      }
    }
  }
}
"""

ANSWER_PROPOSAL = """
mutation addProposalAnswer($componentId: ID!, $proposalId: ID!, $input: AnswerInput!) {
  component(id: $componentId) {
    ... on ProposalsMutation {
      proposal(id: $proposalId) {
        answer(input: $input) {
          id
          state
          answer { translation(locale: "en") }
        }
      }
    }
  }
}
"""

CREATE_MEETING = """
mutation createMeeting($componentId: ID!, $input: CreateMeetingInput!) {
  component(id: $componentId) {
    ... on MeetingsMutation {
      createMeeting(input: $input) {
        id
        title { translation(locale: "en") }
        description { translation(locale: "en") }
        address
      }
    }
  }
}
"""

UPDATE_MEETING = """
mutation updateMeeting($componentId: ID!, $meetingId: ID!, $input: UpdateMeetingInput!) {
  component(id: $componentId) {
    ... on MeetingsMutation {
      meeting(id: $meetingId) {
        update(input: $input) {
          id
          title { translation(locale: "en") }
          description { translation(locale: "en") }
          address
        }
      }
    }
  }
}
"""

WITHDRAW_MEETING = """
mutation withdrawMeeting($componentId: ID!, $meetingId: ID!) {
  component(id: $componentId) {
    ... on MeetingsMutation {
      meeting(id: $meetingId) {
        withdraw(input: {}) {
          id
          withdrawnAt
        }
      }
    }
  }
}
"""

CLOSE_MEETING = """
mutation closeMeeting($componentId: ID!, $meetingId: ID!, $input: CloseMeetingInput!) {
  component(id: $componentId) {
    ... on MeetingsMutation {
      meeting(id: $meetingId) {
        close(input: $input) {
          id
        }
      }
    }
  }
}
"""

CREATE_DEBATE = """
mutation createDebate($componentId: ID!, $input: CreateDebateInput!) {
  component(id: $componentId) {
    ... on DebatesMutation {
      createDebate(input: $input) {
        id
        title { translation(locale: "en") }
        description { translation(locale: "en") }
      }
    }
  }
}
"""

UPDATE_DEBATE = """
mutation updateDebate($componentId: ID!, $debateId: ID!, $input: UpdateDebateInput!) {
  component(id: $componentId) {
    ... on DebatesMutation {
      debate(id: $debateId) {
        update(input: $input) {
          id
          title { translation(locale: "en") }
          description { translation(locale: "en") }
        }
      }
    }
  }
}
"""

CLOSE_DEBATE = """
mutation closeDebate($componentId: ID!, $debateId: ID!, $input: CloseDebateInput!) {
  component(id: $componentId) {
    ... on DebatesMutation {
      debate(id: $debateId) {
        close(input: $input) {
          id
        }
      }
    }
  }
}
"""

# Future/admin API surface. Stock Decidim does not expose these mutations today;
# the CLI keeps them as first-class commands so a Decidim module or upstream PR
# can be exercised without changing the agent-facing interface.

CREATE_PARTICIPATORY_PROCESS = """
mutation createParticipatoryProcess($input: CreateParticipatoryProcessInput!) {
  createParticipatoryProcess(input: $input) {
    id
    slug
    title { translation(locale: "en") }
  }
}
"""

UPDATE_PARTICIPATORY_PROCESS = """
mutation updateParticipatoryProcess($processId: ID!, $input: UpdateParticipatoryProcessInput!) {
  participatoryProcess(id: $processId) {
    update(input: $input) {
      id
      slug
      title { translation(locale: "en") }
    }
  }
}
"""

PUBLISH_PARTICIPATORY_PROCESS = """
mutation publishParticipatoryProcess($processId: ID!) {
  participatoryProcess(id: $processId) {
    publish(input: {}) {
      id
      publishedAt
    }
  }
}
"""

CREATE_PROCESS_PHASE = """
mutation createProcessPhase($processId: ID!, $input: CreateProcessPhaseInput!) {
  participatoryProcess(id: $processId) {
    createPhase(input: $input) {
      id
      title { translation(locale: "en") }
      startDate
      endDate
    }
  }
}
"""

CREATE_COMPONENT = """
mutation createComponent($spaceId: ID!, $input: CreateComponentInput!) {
  participatorySpace(id: $spaceId) {
    createComponent(input: $input) {
      id
      name { translation(locale: "en") }
      manifestName
    }
  }
}
"""

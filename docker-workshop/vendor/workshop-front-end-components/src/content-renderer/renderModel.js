const PAGE_TYPES = new Set([
  'narrative',
  'stage-flow',
  'editor',
  // New workshop flow page types
  'intro-page',
  'review',
  'scrollable-demo'
]);
const BLOCK_TYPES = new Set([
  'markdown',
  'callout',
  'statusPanel',
  'actionRow',
  'stepList',
  'editorStepList',
  'codeSnippet',
  'widget'
]);

function unique(values) {
  return [...new Set(values)];
}

function getTokenValue(tokens, tokenName) {
  return tokenName.split('.').reduce((value, part) => {
    if (value === null || value === undefined) {
      return undefined;
    }

    if (Object.prototype.hasOwnProperty.call(Object(value), part)) {
      return value[part];
    }

    return undefined;
  }, tokens);
}

function createStringResolver(tokens, missingTokens) {
  return value => {
    if (typeof value !== 'string') {
      return value ?? '';
    }

    return value.replace(/\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}/g, (match, tokenName) => {
      const tokenValue = getTokenValue(tokens, tokenName);
      if (tokenValue === undefined || tokenValue === null) {
        missingTokens.push(tokenName);
        return match;
      }

      return String(tokenValue);
    });
  };
}

function mapAction(action, context, resolveString) {
  if (!action || typeof action !== 'object') {
    return null;
  }

  return {
    id: action.id,
    label: resolveString(action.label || action.id || 'Action'),
    args: action.args || {},
    context
  };
}

function mapBlock(block, context, resolveString, missingTokens, errors) {
  if (!block || !BLOCK_TYPES.has(block.type)) {
    errors.push(`Unsupported block type: ${block?.type || 'unknown'}`);
    return null;
  }

  const blockContext = {
    ...context,
    blockType: block.type
  };

  if (block.type === 'markdown') {
    return {
      type: 'markdown',
      body: resolveString(block.body)
    };
  }

  if (block.type === 'callout') {
    return {
      type: 'callout',
      tone: block.tone || 'info',
      title: block.title || '',
      body: resolveString(block.body),
      actions: (block.actions || [])
        .map(action => mapAction(action, blockContext, resolveString))
        .filter(Boolean)
    };
  }

  if (block.type === 'statusPanel') {
    return {
      type: 'statusPanel',
      tone: block.tone || 'info',
      title: block.title || '',
      body: resolveString(block.body),
      actions: (block.actions || [])
        .map(action => mapAction(action, blockContext, resolveString))
        .filter(Boolean)
    };
  }

  if (block.type === 'actionRow') {
    return {
      type: 'actionRow',
      actions: (block.actions || [])
        .map(action => mapAction(action, blockContext, resolveString))
        .filter(Boolean)
    };
  }

  if (block.type === 'codeSnippet') {
    return {
      type: 'codeSnippet',
      language: block.language || 'text',
      title: block.title || '',
      caption: resolveString(block.caption || ''),
      code: block.code || ''
    };
  }

  if (block.type === 'widget') {
    return {
      type: 'widget',
      widgetId: block.widgetId
    };
  }

  if (block.type === 'stepList') {
    return {
      type: 'stepList',
      listId: block.listId,
      variant: block.variant || 'ordered',
      items: (block.items || []).map(item => ({
        itemId: item.itemId,
        title: item.title || '',
        body: resolveString(item.body),
        hint: resolveString(item.hint || ''),
        actions: (item.actions || [])
          .map(action => mapAction(action, {
            ...blockContext,
            listId: block.listId,
            itemId: item.itemId
          }, resolveString))
          .filter(Boolean),
        supportingBlocks: (item.supportingBlocks || [])
          .map(supportingBlock => mapBlock(
            supportingBlock,
            {
              ...blockContext,
              listId: block.listId,
              itemId: item.itemId,
              parentBlockType: 'stepList'
            },
            resolveString,
            missingTokens,
            errors
          ))
          .filter(Boolean)
      }))
    };
  }

  if (block.type === 'editorStepList') {
    return {
      type: 'editorStepList',
      listId: block.listId,
      title: block.title || '',
      description: resolveString(block.description || ''),
      startAt: Number.isFinite(block.startAt) ? block.startAt : 1,
      progressGroup: block.progressGroup || '',
      items: (block.items || []).map(item => ({
        itemId: item.itemId,
        body: resolveString(item.body),
        hint: resolveString(item.hint || ''),
        action: mapAction(item.action, {
          ...blockContext,
          listId: block.listId,
          itemId: item.itemId
        }, resolveString)
      }))
    };
  }

  errors.push(`Unsupported block type: ${block.type}`);
  return null;
}

function mapSection(section, context, resolveString, missingTokens, errors) {
  return {
    sectionId: section.sectionId,
    title: section.title || '',
    body: resolveString(section.body || ''),
    blocks: (section.blocks || [])
      .map(block => mapBlock(block, {
        ...context,
        sectionId: section.sectionId
      }, resolveString, missingTokens, errors))
      .filter(Boolean)
  };
}

function getActiveStage(content, activeStageId, errors) {
  const stages = Array.isArray(content.stages) ? content.stages : [];
  if (!stages.length) {
    errors.push('Stage-flow content requires at least one stage.');
    return null;
  }

  if (!activeStageId) {
    return stages[0];
  }

  const activeStage = stages.find(stage => stage.stageId === activeStageId);
  if (!activeStage) {
    errors.push(`Unknown stage id: ${activeStageId}`);
    return stages[0];
  }

  return activeStage;
}

export function getStageNavItems(content) {
  if (content?.header?.stageNav?.steps?.length) {
    return content.header.stageNav.steps.map(step => ({
      stageId: step.stageId,
      label: step.label || step.stageId
    }));
  }

  if (Array.isArray(content?.stages)) {
    return content.stages.map(stage => ({
      stageId: stage.stageId,
      label: stage.title || stage.stageId
    }));
  }

  return [];
}

export function createContentRenderModel(content, options = {}) {
  const errors = [];
  const missingTokens = [];
  const tokens = options.tokens || {};
  const resolveString = createStringResolver(tokens, missingTokens);

  if (!content || typeof content !== 'object') {
    return {
      viewId: '',
      pageType: '',
      title: '',
      summary: '',
      sections: [],
      stage: null,
      stageNavItems: [],
      errors: ['Content payload must be an object.'],
      missingTokens: []
    };
  }

  if (!PAGE_TYPES.has(content.pageType)) {
    errors.push(`Unsupported page type: ${content.pageType || 'unknown'}`);
  }

  const stage = content.pageType === 'stage-flow'
    ? getActiveStage(content, options.activeStageId, errors)
    : null;
  const sectionsSource = stage ? stage.sections : content.sections;
  const sections = Array.isArray(sectionsSource)
    ? sectionsSource.map(section => mapSection(
      section,
      {
        viewId: content.viewId,
        pageType: content.pageType,
        stageId: stage?.stageId || null
      },
      resolveString,
      missingTokens,
      errors
    ))
    : [];

  if (!sections.length) {
    errors.push('No renderable sections were found for this view.');
  }

  return {
    viewId: content.viewId || '',
    route: content.route || '',
    pageType: content.pageType || '',
    title: content.title || '',
    summary: resolveString(content.summary || ''),
    stage: stage
      ? {
        stageId: stage.stageId,
        title: stage.title || ''
      }
      : null,
    sections,
    header: content.header || {},
    stageNavItems: getStageNavItems(content),
    errors: unique(errors),
    missingTokens: unique(missingTokens)
  };
}

export function bindContentAction(actionHandlers, payload) {
  const handler = actionHandlers?.[payload.actionId];
  if (typeof handler === 'function') {
    return handler(payload);
  }

  return undefined;
}

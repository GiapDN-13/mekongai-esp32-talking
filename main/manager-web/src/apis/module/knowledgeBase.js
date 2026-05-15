import { getServiceUrl } from '../serviceUrl';
import RequestService from '../httpRequest';

function getKnowledgeBaseServiceUrl() {
  return process.env.VUE_APP_KB_API_BASE_URL || getServiceUrl();
}

/**
 * Get auth token
 */
function getAuthToken() {
  return localStorage.getItem('token') || '';
}

/**
 * Generic API request wrapper
 * @param {Object} config - Request configuration
 * @param {string} config.url - Request URL
 * @param {string} config.method - HTTP method
 * @param {Object} [config.data] - Request payload
 * @param {Object} [config.headers] - Additional headers
 * @param {Function} config.callback - Success callback
 * @param {Function} [config.errorCallback] - Error callback
 * @param {string} [config.errorMessage] - Error message
 * @param {Function} [config.retryFunction] - Retry function
 */
function makeApiRequest(config) {
  const token = getAuthToken();
  const { url, method, data, headers, callback, errorCallback, errorMessage, retryFunction } = config;

  const requestBuilder = RequestService.sendRequest()
    .url(url)
    .method(method)
    .header({
      'Authorization': `Bearer ${token}`,
      ...headers
    });

  if (data) {
    requestBuilder.data(data);
  }

  requestBuilder
    .success((res) => {
      RequestService.clearRequestTime();
      callback(res);
    })
    .fail((err) => {
      console.error(errorMessage || 'Operation failed', err);
      if (errorCallback) {
        errorCallback(err);
      }
    })
    .networkFail(() => {
      if (retryFunction) {
        RequestService.reAjaxFun(() => {
          retryFunction();
        });
      }
    }).send();
}

/**
 * Knowledge base management API
 */
export default {
  /**
   * Get knowledge base list
   * @param {Object} params - Query params
   * @param {Function} callback
   * @param {Function} errorCallback
   */
  getKnowledgeBaseList(params, callback, errorCallback) {
    const queryParams = new URLSearchParams({
      page: params.page,
      page_size: params.page_size,
      name: params.name || ''
    }).toString();

    makeApiRequest({
      url: `${getKnowledgeBaseServiceUrl()}/datasets?${queryParams}`,
      method: 'GET',
      callback: callback,
      errorCallback: errorCallback,
      errorMessage: 'Failed to get knowledge base list',
      retryFunction: () => this.getKnowledgeBaseList(params, callback, errorCallback)
    });
  },

  /**
   * Create knowledge base
   * @param {Object} data - Knowledge base data
   * @param {Function} callback
   * @param {Function} errorCallback
   */
  createKnowledgeBase(data, callback, errorCallback) {
    console.log('createKnowledgeBase called with data:', data);
    console.log('API URL:', `${getKnowledgeBaseServiceUrl()}/datasets`);

    makeApiRequest({
      url: `${getKnowledgeBaseServiceUrl()}/datasets`,
      method: 'POST',
      data: data,
      headers: { 'Content-Type': 'application/json' },
      callback: (res) => {
        console.log('createKnowledgeBase success response:', res);
        callback(res);
      },
      errorCallback: (err) => {
        console.error('Failed to create knowledge base:', err);
        if (err.response) {
          console.error('Error response data:', err.response.data);
          console.error('Error response status:', err.response.status);
        }
        if (errorCallback) {
          errorCallback(err);
        }
      },
      errorMessage: 'Failed to create knowledge base',
      retryFunction: () => this.createKnowledgeBase(data, callback, errorCallback)
    });
  },

  /**
   * Update knowledge base
   * @param {string} datasetId - Knowledge base ID
   * @param {Object} data - Update data
   * @param {Function} callback
   * @param {Function} errorCallback
   */
  updateKnowledgeBase(datasetId, data, callback, errorCallback) {
    console.log('updateKnowledgeBase called with datasetId:', datasetId, 'data:', data);
    console.log('API URL:', `${getKnowledgeBaseServiceUrl()}/datasets/${datasetId}`);

    makeApiRequest({
      url: `${getKnowledgeBaseServiceUrl()}/datasets/${datasetId}`,
      method: 'PUT',
      data: data,
      headers: { 'Content-Type': 'application/json' },
      callback: callback,
      errorCallback: errorCallback,
      errorMessage: 'Failed to update knowledge base',
      retryFunction: () => this.updateKnowledgeBase(datasetId, data, callback, errorCallback)
    });
  },

  /**
   * Delete single knowledge base
   * @param {string} datasetId - Knowledge base ID
   * @param {Function} callback
   * @param {Function} errorCallback
   */
  deleteKnowledgeBase(datasetId, callback, errorCallback) {
    console.log('deleteKnowledgeBase called with datasetId:', datasetId);
    console.log('API URL:', `${getKnowledgeBaseServiceUrl()}/datasets/${datasetId}`);

    makeApiRequest({
      url: `${getKnowledgeBaseServiceUrl()}/datasets/${datasetId}`,
      method: 'DELETE',
      callback: callback,
      errorCallback: errorCallback,
      errorMessage: 'Failed to delete knowledge base',
      retryFunction: () => this.deleteKnowledgeBase(datasetId, callback, errorCallback)
    });
  },

  /**
   * Batch delete knowledge bases
   * @param {string|Array} ids - Knowledge base ID string or array
   * @param {Function} callback
   * @param {Function} errorCallback
   */
  deleteKnowledgeBases(ids, callback, errorCallback) {
    const idsStr = Array.isArray(ids) ? ids.join(',') : ids;

    makeApiRequest({
      url: `${getKnowledgeBaseServiceUrl()}/datasets/batch?ids=${idsStr}`,
      method: 'DELETE',
      callback: callback,
      errorCallback: errorCallback,
      errorMessage: 'Failed to batch delete knowledge bases',
      retryFunction: () => this.deleteKnowledgeBases(ids, callback, errorCallback)
    });
  },

  /**
   * Get document list
   * @param {string} datasetId - Knowledge base ID
   * @param {Object} params - Query params
   * @param {Function} callback
   * @param {Function} errorCallback
   */
  getDocumentList(datasetId, params, callback, errorCallback) {
    const queryParams = new URLSearchParams({
      page: params.page,
      page_size: params.page_size,
      name: params.name || ''
    }).toString();

    makeApiRequest({
      url: `${getKnowledgeBaseServiceUrl()}/datasets/${datasetId}/documents?${queryParams}`,
      method: 'GET',
      callback: callback,
      errorCallback: errorCallback,
      errorMessage: 'Failed to get document list',
      retryFunction: () => this.getDocumentList(datasetId, params, callback, errorCallback)
    });
  },

  /**
   * Upload document
   * @param {string} datasetId - Knowledge base ID
   * @param {Object} formData - Form data
   * @param {Function} callback
   * @param {Function} errorCallback
   */
  uploadDocument(datasetId, formData, callback, errorCallback) {
    const token = getAuthToken();
    const url = `${getKnowledgeBaseServiceUrl()}/datasets/${datasetId}/documents`;

    fetch(url, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData,
    })
      .then(async (resp) => {
        const json = await resp.json();
        RequestService.clearRequestTime();
        callback({ data: json });
      })
      .catch((err) => {
        console.error('Failed to upload document', err);
        if (errorCallback) errorCallback(err);
      });
  },

  /**
   * Parse document
   * @param {string} datasetId - Knowledge base ID
   * @param {string} documentId - Document ID
   * @param {Function} callback
   * @param {Function} errorCallback
   */
  parseDocument(datasetId, documentId, callback, errorCallback) {
    const requestBody = {
      document_ids: [documentId]
    };

    makeApiRequest({
      url: `${getKnowledgeBaseServiceUrl()}/datasets/${datasetId}/chunks`,
      method: 'POST',
      data: requestBody,
      headers: { 'Content-Type': 'application/json' },
      callback: callback,
      errorCallback: errorCallback,
      errorMessage: 'Failed to parse document',
      retryFunction: () => this.parseDocument(datasetId, documentId, callback, errorCallback)
    });
  },

  /**
   * Delete document
   * @param {string} datasetId - Knowledge base ID
   * @param {string} documentId - Document ID
   * @param {Function} callback
   * @param {Function} errorCallback
   */
  deleteDocument(datasetId, documentId, callback, errorCallback) {
    makeApiRequest({
      url: `${getKnowledgeBaseServiceUrl()}/datasets/${datasetId}/documents/${documentId}`,
      method: 'DELETE',
      callback: callback,
      errorCallback: errorCallback,
      errorMessage: 'Failed to delete document',
      retryFunction: () => this.deleteDocument(datasetId, documentId, callback, errorCallback)
    });
  },

  /**
   * List document chunks
   * @param {string} datasetId - Knowledge base ID
   * @param {string} documentId - Document ID
   * @param {Object} params - Query params
   * @param {Function} callback
   * @param {Function} errorCallback
   */
  listChunks(datasetId, documentId, params, callback, errorCallback) {
    let queryParams = new URLSearchParams({
      page: params.page || 1,
      page_size: params.page_size || 10
    }).toString();

    if (params.keywords) {
      queryParams += `&keywords=${encodeURIComponent(params.keywords)}`;
    }

    makeApiRequest({
      url: `${getKnowledgeBaseServiceUrl()}/datasets/${datasetId}/documents/${documentId}/chunks?${queryParams}`,
      method: 'GET',
      callback: callback,
      errorCallback: errorCallback,
      errorMessage: 'Failed to get chunk list',
      retryFunction: () => this.listChunks(datasetId, documentId, params, callback, errorCallback)
    });
  },

  /**
   * Retrieval test
   * @param {string} datasetId - Knowledge base ID
   * @param {Object} data - Retrieval test params
   * @param {Function} callback
   * @param {Function} errorCallback
   */
  retrievalTest(datasetId, data, callback, errorCallback) {
    makeApiRequest({
      url: `${getKnowledgeBaseServiceUrl()}/datasets/${datasetId}/retrieval-test`,
      method: 'POST',
      data: data,
      headers: { 'Content-Type': 'application/json' },
      callback: callback,
      errorCallback: errorCallback,
      errorMessage: 'Retrieval test failed',
      retryFunction: () => this.retrievalTest(datasetId, data, callback, errorCallback)
    });
  }

};

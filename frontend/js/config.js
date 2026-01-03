const CONFIG = {
    API_BASE_URL: 'http://localhost:8000/api/v1',
    SURVEY_ID: 'Immigration Policy Opinion Survey',
    DEBUG: true
};

const log = (...args) => {
    if (CONFIG.DEBUG) {
        console.log('[Survey App]', ...args);
    }
};

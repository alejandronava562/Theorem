/**
 * Progress Tracker Module
 *
 * Handles all progress tracking functionality:
 * - Saves learning path to Firestore
 * - Saves session state (progress, coins, active unit, etc.)
 * - Loads saved progress on page reload
 * - Provides resume functionality
 */

const ProgressTracker = (() => {
  // Private state
  let currentTopic = null;
  let autoSaveInterval = null;
  const AUTO_SAVE_INTERVAL = 30000; // Save every 30 seconds

  /**
   * Initialize progress tracker with auto-save
   * Should be called once on app startup
   */
  function init() {
    // Start auto-save timer if user is authenticated
    if (document.querySelector("#user-info:not(.hidden)")) {
      startAutoSave();
    }
  }

  /**
   * Start auto-save for current topic
   */
  function startAutoSave() {
    if (autoSaveInterval) clearInterval(autoSaveInterval);
    autoSaveInterval = setInterval(() => {
      if (currentTopic) {
        saveCurrentProgress();
      }
    }, AUTO_SAVE_INTERVAL);
  }

  /**
   * Save current session progress to Firestore
   * @param {Object} sessionData - Current session state from app.js
   */
  async function saveProgress(sessionData) {
    const { topic, progress, coins, activeUnitId } = sessionData;

    if (!topic) return;
    currentTopic = topic;

    try {
      const response = await fetch("/api/save-progress", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          progress,
          coins,
          active_unit_id: activeUnitId,
        }),
      });

      if (!response.ok) {
        console.warn("Failed to save progress:", response.status);
      }
    } catch (err) {
      console.error("Error saving progress:", err);
    }
  }

  /**
   * Save complete session state (for mid-quiz recovery)
   * @param {string} topic - Current topic
   * @param {Object} sessionData - Complete session state
   */
  async function saveSession(topic, sessionData) {
    if (!topic) return;
    currentTopic = topic;

    try {
      const response = await fetch("/api/save-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          session: sessionData,
        }),
      });

      if (!response.ok) {
        console.warn("Failed to save session:", response.status);
      }
    } catch (err) {
      console.error("Error saving session:", err);
    }
  }

  /**
   * Load saved progress for a topic
   * @param {string} topic - Topic name
   * @returns {Object|null} Saved progress or null
   */
  async function loadProgress(topic) {
    try {
      const response = await fetch(`/api/load-progress/${topic}`);
      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      console.error("Error loading progress:", err);
    }
    return null;
  }

  /**
   * Load saved session state for a topic
   * @param {string} topic - Topic name
   * @returns {Object|null} Saved session or null
   */
  async function loadSession(topic) {
    try {
      const response = await fetch(`/api/load-session/${topic}`);
      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      console.error("Error loading session:", err);
    }
    return null;
  }

  /**
   * Get list of all topics user has started
   * @returns {Array} List of topic names
   */
  async function getTopics() {
    try {
      const response = await fetch("/api/topics");
      if (response.ok) {
        const data = await response.json();
        return data.topics || [];
      }
    } catch (err) {
      console.error("Error getting topics:", err);
    }
    return [];
  }

  /**
   * Internal function to save current progress periodically
   */
  async function saveCurrentProgress() {
    // This would be called by the app to save current state
    // The app should pass the session data
    // Example: ProgressTracker.saveProgress(current);
  }

  /**
   * Clean up when user logs out
   */
  function cleanup() {
    if (autoSaveInterval) {
      clearInterval(autoSaveInterval);
      autoSaveInterval = null;
    }
    currentTopic = null;
  }

  // Public API
  return {
    init,
    startAutoSave,
    saveProgress,
    saveSession,
    loadProgress,
    loadSession,
    getTopics,
    cleanup,
  };
})();

// Export for use in app.js
if (typeof module !== "undefined" && module.exports) {
  module.exports = ProgressTracker;
}

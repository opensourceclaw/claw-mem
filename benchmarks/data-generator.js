"use strict";
// DataGenerator - Synthetic test data generation (v6.32.0)
Object.defineProperty(exports, "__esModule", { value: true });
exports.DataGenerator = void 0;
const random_js_1 = require("./random.js");
// Template pools (20+ per type)
const FACT_TEMPLATES = [
    "User prefers {theme} theme for {app}",
    "Project {project} uses {tech} for {purpose}",
    "Meeting with {person} about {topic} on {date}",
    "Bug #{bugId} was fixed in {component}",
    "Feature {feature} was implemented in version {version}",
    "User {name} can be reached at {email}",
    "API endpoint {endpoint} returns {returnType}",
    "Database {database} is hosted on {host}",
    "Configuration setting {setting} is set to {value}",
    "User's timezone is {timezone}",
    "Language preference is {language}",
    "Notification setting for {event} is {status}",
    "Default editor is {editor}",
    "Repository {repo} is located at {url}",
    "Service {service} runs on port {port}",
    "Authentication method is {authMethod}",
    "Cache duration for {cacheType} is {duration}",
    "Rate limit for {apiName} is {rateLimit}",
    "Backup schedule for {resource} is {schedule}",
    "Log level for {module} is {logLevel}",
];
const PREFERENCE_TEMPLATES = [
    "User prefers {option_a} over {option_b}",
    "Default {setting} is {value}",
    "Theme preference is {theme}",
    "Editor font size is {fontSize}",
    "Auto-save interval is {interval}",
    "Tab width preference is {tabWidth}",
    "Indent style is {indentStyle}",
    "Color scheme is {colorScheme}",
    "Language is set to {language}",
    "Timezone is {timezone}",
    "Date format is {dateFormat}",
    "Number format is {numberFormat}",
    "Currency is {currency}",
    "Notification preference is {notifPref}",
    "Privacy setting is {privacyLevel}",
    "Accessibility mode is {a11yMode}",
    "Display density is {density}",
    "Animation preference is {animPref}",
    "Sound preference is {soundPref}",
    "Auto-update is {autoUpdate}",
];
const EVENT_TEMPLATES = [
    "Deployed version {version} to {environment}",
    "Fixed bug #{bugId} in {component}",
    "Released feature {feature}",
    "Updated documentation for {module}",
    "Merged pull request #{prId}",
    "Created branch {branchName}",
    "Deleted stale data from {table}",
    "Ran migration {migrationId}",
    "Configured {service} for {purpose}",
    "Started {processName} process",
    "Stopped {serviceName} service",
    "Backed up {resource}",
    "Restored {resource} from backup",
    "Upgraded {package} to {version}",
    "Downgraded {package} to {version}",
    "Added user {username}",
    "Removed user {username}",
    "Changed permission for {resource}",
    "Rotated credentials for {service}",
    "Audited {module} module",
];
const DISTRACTION_TEMPLATES = [
    "Random thought about {topic}",
    "Unrelated note regarding {subject}",
    "Temporary observation: {observation}",
    "Quick note: {note}",
    "Miscellaneous item: {item}",
    "Passing mention of {thing}",
    "Casual reference to {reference}",
    "Off-topic comment: {comment}",
    "Irrelevant detail: {detail}",
    "Background noise: {noise}",
    "Side note about {sideTopic}",
    "Tangential mention of {tangent}",
    "Unconnected fact: {fact}",
    "Non-sequential item: {nonSeqItem}",
    "Disparate record: {record}",
    "Isolated entry: {entry}",
    "Detached observation: {detObs}",
    "Separate note: {sepNote}",
    "Independent item: {indItem}",
    "Unassociated record: {unassoc}",
];
// Value pools for template filling
const VALUE_POOLS = {
    theme: ["dark", "light", "solarized", "monokai", "gruvbox", "nord", "dracula"],
    app: ["VSCode", "Vim", "Emacs", "IntelliJ", "Sublime", "Atom", "Nova"],
    project: ["claw-mem", "claw-ctx", "claw-cog", "openclaw", "devclaw", "neoclaw"],
    tech: ["TypeScript", "Python", "Rust", "Go", "Java", "Kotlin", "Swift"],
    purpose: ["backend", "frontend", "testing", "deployment", "monitoring", "analytics"],
    person: ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"],
    topic: ["architecture", "performance", "security", "UX", "API design", "integration"],
    date: ["2026-01-15", "2026-02-20", "2026-03-10", "2026-04-05", "2026-05-22"],
    component: ["auth", "storage", "retrieval", "indexing", "compression", "caching"],
    feature: ["hybrid-search", "entity-index", "version-chain", "strategy-registry"],
    version: ["v6.30.0", "v6.31.0", "v6.32.0", "v1.0.0", "v2.5.0"],
    language: ["en", "zh", "ja", "ko", "es", "fr", "de"],
    timezone: ["UTC", "Asia/Shanghai", "America/New_York", "Europe/London", "PST", "EST"],
    environment: ["production", "staging", "development", "testing", "preview"],
    setting: ["timeout", "batchSize", "maxRetries", "cacheSize", "logLevel"],
    option_a: ["option1", "option2", "choice1", "choice2", "alternative1"],
    option_b: ["alternative2", "fallback", "backup", "secondary", "default"],
    value: ["true", "false", "enabled", "disabled", "auto"],
    bugId: ["101", "202", "303", "404", "505", "606"],
    email: ["user@example.com", "dev@test.org", "admin@company.io"],
    endpoint: ["/api/users", "/api/data", "/api/config", "/api/health"],
    returnType: ["JSON", "XML", "binary", "text"],
    database: ["users_db", "products_db", "analytics_db", "logs_db"],
    host: ["localhost", "db.server.com", "cloud.db.io"],
    event: ["push", "email", "sms", "webhook"],
    status: ["enabled", "disabled", "pending", "active"],
    editor: ["VSCode", "Vim", "Emacs", "Sublime", "IntelliJ"],
    repo: ["main-repo", "fork-repo", "upstream-repo"],
    url: ["https://github.com/org/repo", "https://gitlab.com/team/project"],
    port: ["3000", "8080", "443", "8000", "5000"],
    authMethod: ["OAuth", "JWT", "API Key", "Basic Auth"],
    cacheType: ["memory", "redis", "file", "database"],
    duration: ["5min", "1hour", "1day", "1week"],
    apiName: ["github", "stripe", "twilio", "sendgrid"],
    rateLimit: ["100/min", "1000/hour", "10000/day"],
    resource: ["database", "storage", "logs", "configs"],
    schedule: ["daily", "weekly", "monthly", "hourly"],
    module: ["auth", "storage", "retrieval", "indexing"],
    logLevel: ["debug", "info", "warn", "error"],
    fontSize: ["12px", "14px", "16px", "18px"],
    interval: ["30s", "1min", "5min", "10min"],
    tabWidth: ["2", "4", "8"],
    indentStyle: ["spaces", "tabs"],
    colorScheme: ["default", "high-contrast", "protanopia", "deuteranopia"],
    dateFormat: ["YYYY-MM-DD", "MM/DD/YYYY", "DD-MM-YYYY"],
    numberFormat: ["1,000.00", "1.000,00", "1 000,00"],
    currency: ["USD", "EUR", "GBP", "JPY", "CNY"],
    notifPref: ["all", "important", "none", "digest"],
    privacyLevel: ["public", "private", "friends", "team"],
    a11yMode: ["off", "screen-reader", "high-contrast", "reduced-motion"],
    density: ["compact", "normal", "comfortable"],
    animPref: ["full", "reduced", "none"],
    soundPref: ["on", "off", "important-only"],
    autoUpdate: ["on", "off", "notify"],
    processName: ["build", "test", "deploy", "lint"],
    serviceName: ["api", "worker", "scheduler", "webhook"],
    package: ["claw-mem", "typescript", "vitest", "eslint"],
    branchName: ["feature/x", "bugfix/y", "release/z"],
    table: ["users", "sessions", "logs", "events"],
    migrationId: ["001", "002", "003", "004"],
    username: ["alice", "bob", "charlie", "admin"],
    observation: ["interesting pattern", "unexpected behavior", "normal flow"],
    note: ["remember this", "todo item", "quick thought"],
    item: ["random item", "misc entry", "temp data"],
    thing: ["something", "anything", "everything"],
    reference: ["doc", "spec", "guide", "manual"],
    comment: ["note to self", "reminder", "observation"],
    detail: ["minor point", "small note", "detail entry"],
    noise: ["background info", "irrelevant data", "noise entry"],
    sideTopic: ["related topic", "side note", "tangent"],
    tangent: ["tangent point", "offshoot", "branch"],
    fact: ["random fact", "unrelated info", "isolated data"],
    nonSeqItem: ["out of order", "non-sequential", "random"],
    record: ["entry record", "data point", "log entry"],
    entry: ["single entry", "isolated record", "standalone"],
    detObs: ["detached note", "separate observation", "independent"],
    sepNote: ["separate item", "distinct entry", "isolated note"],
    indItem: ["independent", "standalone", "self-contained"],
    unassoc: ["unassociated", "disconnected", "unrelated"],
    subject: ["misc subject", "random topic", "unrelated area"],
};
/**
 * Generate synthetic test data for all benchmarks.
 * No external dependencies - all templates embedded.
 */
class DataGenerator {
    rng;
    idCounter = 0;
    constructor(seed) {
        this.rng = new random_js_1.SeededRandom(seed);
    }
    /**
     * Generate facts of different memory types.
     */
    generateFacts(count, types) {
        const facts = [];
        const typeDistribution = this.distributeTypes(count, types);
        for (const [type, typeCount] of Object.entries(typeDistribution)) {
            for (let i = 0; i < typeCount; i++) {
                facts.push(this.generateFact(type));
            }
        }
        return this.rng.shuffle(facts);
    }
    /**
     * Generate temporal event sequence with timestamps.
     */
    generateTemporalEvents(count) {
        const events = [];
        const baseTime = Date.now() - count * 3600000; // count hours ago
        for (let i = 0; i < count; i++) {
            const timestamp = new Date(baseTime + i * 3600000).toISOString();
            const template = this.rng.pick(EVENT_TEMPLATES);
            const content = this.fillTemplate(template);
            events.push({
                id: this.nextId(),
                content,
                memoryType: "episodic",
                tags: ["temporal-event"],
                timestamp,
                metadata: { eventIndex: i },
            });
        }
        return events;
    }
    /**
     * Generate preference pairs: original + updated.
     */
    generatePreferences(count) {
        const original = [];
        const updated = [];
        for (let i = 0; i < count; i++) {
            const prefKey = `pref_${this.rng.randomString(6)}`;
            const template = this.rng.pick(PREFERENCE_TEMPLATES);
            // Original preference
            const originalContent = this.fillTemplate(template);
            original.push({
                id: this.nextId(),
                content: originalContent,
                memoryType: "preference",
                tags: ["preference"],
                metadata: { pref_key: prefKey },
                prefKey,
            });
            // Updated preference (different value)
            const updatedContent = this.fillTemplate(template);
            updated.push({
                id: this.nextId(),
                content: updatedContent,
                memoryType: "preference",
                tags: ["preference"],
                metadata: { pref_key: prefKey, updated: true },
                prefKey,
            });
        }
        return { original, updated };
    }
    /**
     * Generate fact-rich conversations (multiple facts per message).
     */
    generateConversations(count, factsPerConversation) {
        const conversations = [];
        for (let i = 0; i < count; i++) {
            const facts = [];
            for (let j = 0; j < factsPerConversation; j++) {
                facts.push(this.fillTemplate(this.rng.pick(FACT_TEMPLATES)));
            }
            const content = `In this session: ${facts.join(". ")}.`;
            conversations.push({
                id: this.nextId(),
                content,
                memoryType: "episodic",
                tags: ["conversation"],
                metadata: { factsCount: factsPerConversation, embeddedFacts: facts },
            });
        }
        return conversations;
    }
    /**
     * Generate queries targeting specific facts.
     */
    generateQueries(facts, count) {
        const queries = [];
        const selectedFacts = this.rng.shuffle([...facts]).slice(0, count);
        for (const fact of selectedFacts) {
            const queryType = this.rng.pick(["exact", "semantic"]);
            queries.push({
                query: this.generateQueryForFact(fact, queryType),
                expectedAnswer: fact.content,
                relatedFactIndices: [facts.indexOf(fact)],
                queryType,
            });
        }
        return queries;
    }
    /**
     * Generate distraction facts (unrelated to target facts).
     */
    generateDistractions(count) {
        const distractions = [];
        for (let i = 0; i < count; i++) {
            const template = this.rng.pick(DISTRACTION_TEMPLATES);
            distractions.push({
                id: this.nextId(),
                content: this.fillTemplate(template),
                memoryType: "episodic",
                tags: ["distraction"],
            });
        }
        return distractions;
    }
    // Helper methods
    generateFact(memoryType) {
        const template = this.rng.pick(FACT_TEMPLATES);
        const content = this.fillTemplate(template);
        return {
            id: this.nextId(),
            content,
            memoryType,
            tags: [memoryType],
            metadata: {},
        };
    }
    fillTemplate(template) {
        let result = template;
        const placeholders = template.match(/\{(\w+)\}/g) || [];
        for (const ph of placeholders) {
            const key = ph.slice(1, -1);
            const pool = VALUE_POOLS[key];
            if (pool && pool.length > 0) {
                result = result.replace(ph, this.rng.pick(pool));
            }
            else {
                result = result.replace(ph, this.rng.randomString(6));
            }
        }
        return result;
    }
    generateQueryForFact(fact, queryType) {
        const tokens = fact.content.split(/\s+/);
        if (queryType === "exact") {
            // Use a subset of the fact content
            return tokens.slice(0, Math.min(5, tokens.length)).join(" ");
        }
        else {
            // Semantic query: use related keywords
            return tokens.filter(t => t.length > 4).slice(0, 3).join(" ");
        }
    }
    distributeTypes(total, types) {
        const result = {};
        const perType = Math.floor(total / types.length);
        let remainder = total % types.length;
        for (const type of types) {
            result[type] = perType + (remainder > 0 ? 1 : 0);
            remainder--;
        }
        return result;
    }
    nextId() {
        return `fact_${++this.idCounter}_${Date.now()}`;
    }
}
exports.DataGenerator = DataGenerator;
//# sourceMappingURL=data-generator.js.map
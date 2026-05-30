// Copyright 2026 Peter Cheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * DualLayerMemory - Two-layer memory organization above the four-subgraph index.
 *
 * Layer 1 - Event Progression Graph:
 *   Clusters memory nodes into "events" with temporal chains.
 *
 * Layer 2 - Topic Associative Network:
 *   Groups events/nodes into "topics" with semantic links.
 */

export interface Event {
  event_id: string;
  title: string;
  description: string;
  node_ids: string[];
  session_id?: string | null;
  start_time: number;
  end_time?: number | null;
  tags: string[];
}

export interface Topic {
  topic_id: string;
  name: string;
  description: string;
  node_ids: string[];
  event_ids: string[];
  keywords: string[];
  created_at: number;
  updated_at: number;
}

function makeEvent(
  event_id: string,
  title: string,
  description?: string,
  node_ids?: string[],
  session_id?: string | null,
  start_time?: number,
  tags?: string[],
): Event {
  return {
    event_id,
    title,
    description: description ?? "",
    node_ids: node_ids ?? [],
    session_id: session_id ?? null,
    start_time: start_time ?? Date.now() / 1000,
    end_time: null,
    tags: tags ?? [],
  };
}

function makeTopic(
  topic_id: string,
  name: string,
  description?: string,
  node_ids?: string[],
  event_ids?: string[],
  keywords?: string[],
  created_at?: number,
  updated_at?: number,
): Topic {
  return {
    topic_id,
    name,
    description: description ?? "",
    node_ids: node_ids ?? [],
    event_ids: event_ids ?? [],
    keywords: keywords ?? [],
    created_at: created_at ?? Date.now() / 1000,
    updated_at: updated_at ?? Date.now() / 1000,
  };
}

function generateIdWithPrefix(prefix: string): string {
  const hex = "0123456789abcdef";
  let id = "";
  for (let i = 0; i < 12; i++) {
    id += hex[Math.floor(Math.random() * 16)];
  }
  return `${prefix}_${id}`;
}

export class DualLayerMemory {
  private _events: Map<string, Event> = new Map();
  private _topics: Map<string, Topic> = new Map();
  private _eventChain: Map<string, string[]> = new Map(); // event_id -> prev IDs
  private _topicLinks: Map<string, number> = new Map(); // "t1||t2" -> weight

  // ── Layer 1: Event Progression Graph ──

  /**
   * Create a new event. Auto-links to the latest event in the same session.
   */
  addEvent(
    title: string,
    description?: string,
    node_ids?: string[],
    session_id?: string | null,
    tags?: string[],
  ): string {
    const eventId = generateIdWithPrefix("evt");
    const now = Date.now() / 1000;
    const event = makeEvent(
      eventId,
      title,
      description,
      node_ids,
      session_id,
      now,
      tags,
    );

    this._events.set(eventId, event);

    if (session_id) {
      const prev = this.findLatestEventInSession(session_id);
      if (prev) {
        const chain = this._eventChain.get(eventId) ?? [];
        chain.push(prev);
        this._eventChain.set(eventId, chain);
      }
    }

    return eventId;
  }

  private findLatestEventInSession(sessionId: string): string | undefined {
    let bestTime = 0;
    let bestId: string | undefined;
    for (const evt of this._events.values()) {
      if (evt.session_id === sessionId) {
        const t = evt.end_time ?? evt.start_time;
        if (t > bestTime) {
          bestTime = t;
          bestId = evt.event_id;
        }
      }
    }
    return bestId;
  }

  /** Explicitly link two events bidirectionally. */
  linkEvents(event1Id: string, event2Id: string): void {
    const chain1 = this._eventChain.get(event1Id) ?? [];
    if (!chain1.includes(event2Id)) {
      chain1.push(event2Id);
    }
    this._eventChain.set(event1Id, chain1);

    const chain2 = this._eventChain.get(event2Id) ?? [];
    if (!chain2.includes(event1Id)) {
      chain2.push(event1Id);
    }
    this._eventChain.set(event2Id, chain2);
  }

  /** Get event details. */
  getEvent(eventId: string): Event | undefined {
    return this._events.get(eventId);
  }

  /** Get the event chain (predecessor event sequence). */
  getEventChain(eventId: string): Event[] {
    const visited: string[] = [];

    const backtrack = (eid: string) => {
      if (visited.includes(eid) || !this._events.has(eid)) return;
      visited.push(eid);
      for (const prevId of this._eventChain.get(eid) ?? []) {
        backtrack(prevId);
      }
    };

    backtrack(eventId);
    return visited.map((eid) => this._events.get(eid)!);
  }

  /** Find events matching any of the given tags. */
  findEventsByTags(tags: string[]): Event[] {
    const results: Event[] = [];
    for (const evt of this._events.values()) {
      if (tags.some((t) => evt.tags.includes(t))) {
        results.push(evt);
      }
    }
    return results;
  }

  /** Find all events in a session. */
  findEventsBySession(sessionId: string): Event[] {
    const results: Event[] = [];
    for (const evt of this._events.values()) {
      if (evt.session_id === sessionId) {
        results.push(evt);
      }
    }
    results.sort((a, b) => a.start_time - b.start_time);
    return results;
  }

  /** Event count. */
  eventCount(): number {
    return this._events.size;
  }

  // ── Layer 2: Topic Associative Network ──

  /** Create a new topic. */
  addTopic(
    name: string,
    description?: string,
    node_ids?: string[],
    event_ids?: string[],
    keywords?: string[],
  ): string {
    const topicId = generateIdWithPrefix("tpc");
    const now = Date.now() / 1000;
    const topic = makeTopic(
      topicId,
      name,
      description,
      node_ids,
      event_ids,
      keywords,
      now,
      now,
    );

    this._topics.set(topicId, topic);
    return topicId;
  }

  /** Get topic by ID. */
  getTopic(topicId: string): Topic | undefined {
    return this._topics.get(topicId);
  }

  /** Link two topics with a symmetric weight. */
  linkTopics(topic1Id: string, topic2Id: string, weight: number = 0.5): void {
    this._topicLinks.set(`${topic1Id}||${topic2Id}`, weight);
    this._topicLinks.set(`${topic2Id}||${topic1Id}`, weight);
  }

  /** Get related topics above the minimum weight threshold. */
  getRelatedTopics(
    topicId: string,
    minWeight: number = 0.3,
  ): [Topic, number][] {
    const results: [Topic, number][] = [];
    for (const [key, w] of this._topicLinks) {
      const [t1, t2] = key.split("||");
      if (t1 === topicId && w >= minWeight && this._topics.has(t2)) {
        results.push([this._topics.get(t2)!, w]);
      }
    }
    return results.sort((a, b) => b[1] - a[1]);
  }

  /** Search topics by keywords. Returns topics ordered by match count. */
  searchByKeywords(keywords: string[]): Topic[] {
    const kwSet = new Set(keywords.map((k) => k.toLowerCase()));
    const scored: [Topic, number][] = [];

    for (const topic of this._topics.values()) {
      const topicKwSet = new Set(topic.keywords.map((k) => k.toLowerCase()));
      let score = 0;
      for (const kw of kwSet) {
        if (topicKwSet.has(kw)) score++;
      }
      if (score > 0) {
        scored.push([topic, score]);
      }
    }

    return scored.sort((a, b) => b[1] - a[1]).map(([t]) => t);
  }

  /** Topic count. */
  topicCount(): number {
    return this._topics.size;
  }

  // ── Persistence ──

  toDict(): Record<string, unknown> {
    return {
      events: Object.fromEntries(this._events),
      topics: Object.fromEntries(this._topics),
      event_chain: Object.fromEntries(this._eventChain),
      topic_links: Object.fromEntries(this._topicLinks),
    };
  }

  static fromDict(d: Record<string, any>): DualLayerMemory {
    const dm = new DualLayerMemory();
    dm._events = new Map(Object.entries(d.events ?? {}));
    dm._topics = new Map(Object.entries(d.topics ?? {}));

    const ec = d.event_chain ?? {};
    for (const [k, v] of Object.entries(ec)) {
      dm._eventChain.set(k, v as string[]);
    }

    const tl = d.topic_links ?? {};
    for (const [k, v] of Object.entries(tl)) {
      dm._topicLinks.set(k, v as number);
    }

    return dm;
  }
}

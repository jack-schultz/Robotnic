(function () {
    const CREATORS = [
        { id: "hangout", name: "➕ Hangout", template: "{user}'s Room", limit: 0, access: "public" },
        { id: "gaming", name: "➕ Gaming", template: "{activity} Lobby", limit: 5, access: "public" },
        { id: "study", name: "➕ Study", template: "Study with {user}", limit: 4, access: "public" },
        { id: "private", name: "➕ Private", template: "{user}'s Room", limit: 2, access: "lock" },
    ];

    const USERS = {
        Alex: { color: "#5865f2", activity: null, id: "482910334821990401" },
        Blake: { color: "#eb459e", activity: null, id: "482910334821990402" },
        Casey: { color: "#23a559", activity: "Valorant", id: "591028441002331018" },
        Drew: { color: "#f0b232", activity: null, id: "602119552113442129" },
    };

    const ICON_SPEAKER = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3a4.5 4.5 0 0 0-2.5-4.03v8.06A4.5 4.5 0 0 0 16.5 12z"/></svg>';
    const ICON_LOCK = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 10V7a5 5 0 0 1 10 0v3h1a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h1zm2 0h6V7a3 3 0 0 0-6 0v3z"/></svg>';
    const ICON_HIDE = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 3l18 18"/><path d="M10.6 6.1A10 10 0 0 1 12 6c5 0 9 6 9 6a17 17 0 0 1-3.2 3.7"/><path d="M6.1 6.1C3.5 8 2 12 2 12s4 6 10 6c1.3 0 2.5-.3 3.6-.8"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>';

    const CONTROL_IDS = ["ctrl-rename", "ctrl-limit", "ctrl-give", "ctrl-mute", "ctrl-deafen", "ctrl-ban", "ctrl-clear", "ctrl-delete", "ctrl-public", "ctrl-lock", "ctrl-hide"];

    const state = {
        actor: null,
        view: { type: "offline" },
        rooms: [],
        log: [],
        status: "",
        nextId: 4,
        timers: [],
    };

    function el(tag, attrs, children) {
        const node = document.createElement(tag);
        if (attrs) {
            Object.keys(attrs).forEach(function (key) {
                const value = attrs[key];
                if (value == null || value === false) return;
                if (key === "class") node.className = value;
                else if (key === "text") node.textContent = value;
                else if (key.indexOf("on") === 0 && typeof value === "function") {
                    node.addEventListener(key.slice(2).toLowerCase(), value);
                } else node.setAttribute(key, value === true ? "" : String(value));
            });
        }
        (children || []).forEach(function (child) {
            if (child == null) return;
            node.append(child.nodeType ? child : document.createTextNode(String(child)));
        });
        return node;
    }

    function later(fn, ms) {
        const id = setTimeout(fn, ms);
        state.timers.push(id);
        return id;
    }

    function clearTimers() {
        state.timers.forEach(clearTimeout);
        state.timers = [];
    }

    function clock(date) {
        return [date.getHours(), date.getMinutes(), date.getSeconds()]
            .map(function (part) { return String(part).padStart(2, "0"); })
            .join(":");
    }

    function discordStamp(date) {
        let hours = date.getHours();
        const minutes = String(date.getMinutes()).padStart(2, "0");
        const suffix = hours >= 12 ? "PM" : "AM";
        hours = hours % 12 || 12;
        return "Today at " + hours + ":" + minutes + " " + suffix;
    }

    function $(id) {
        return document.getElementById(id);
    }

    function creatorById(id) {
        return CREATORS.filter(function (creator) { return creator.id === id; })[0];
    }

    function roomById(id) {
        return state.rooms.filter(function (room) { return room.id === id; })[0] || null;
    }

    function roomContaining(name) {
        return state.rooms.filter(function (room) { return room.members.indexOf(name) !== -1; })[0] || null;
    }

    function currentRoom() {
        if (state.view.type !== "room") return null;
        return roomById(state.view.id);
    }

    function activityText(room) {
        const names = [];
        room.members.forEach(function (name) {
            const activity = USERS[name] && USERS[name].activity;
            if (activity && names.indexOf(activity) === -1) names.push(activity);
        });
        if (!names.length) return "General";
        names.sort(function (a, b) { return a.length - b.length; });
        return names.join(", ");
    }

    function channelName(room) {
        if (room.customName) return room.customName;
        const creator = creatorById(room.creatorId);
        return creator.template
            .split("{user}").join(room.owner || "Public")
            .split("{activity}").join(activityText(room))
            .split("{count}").join(String(room.count));
    }

    function canControl(room) {
        return Boolean(room && state.actor && room.owner === state.actor && room.members.indexOf(state.actor) !== -1);
    }

    function logEvent(entry) {
        entry.stamp = discordStamp(new Date());
        state.log.push(entry);
    }

    function logRemove(room, userName, channelLabel) {
        logEvent({
            kind: "channel_remove",
            channelName: channelLabel,
            channelId: room.discordId,
            userName: userName,
            userId: USERS[userName].id,
        });
    }

    function setVariant(button, variant) {
        button.classList.remove("dc-btn--primary", "dc-btn--success", "dc-btn--secondary", "dc-btn--danger");
        button.classList.add("dc-btn--" + variant);
    }

    function seed() {
        clearTimers();
        state.actor = null;
        state.view = { type: "offline" };
        state.log = [];
        state.status = "";
        state.nextId = 4;
        state.rooms = [
            {
                id: "r1",
                discordId: "853490879753617001",
                creatorId: "hangout",
                count: 1,
                customName: null,
                limit: 0,
                access: "public",
                members: ["Alex", "Blake"],
                owner: "Alex",
                muted: {},
                deafened: {},
                banned: [],
                notes: [],
                mention: false,
                mentionFading: false,
                stamp: "Today at 9:02 PM",
            },
            {
                id: "r2",
                discordId: "853490879753617002",
                creatorId: "gaming",
                count: 1,
                customName: null,
                limit: 5,
                access: "public",
                members: ["Casey"],
                owner: "Casey",
                muted: {},
                deafened: {},
                banned: [],
                notes: [],
                mention: false,
                mentionFading: false,
                stamp: "Today at 9:04 PM",
            },
            {
                id: "r3",
                discordId: "853490879753617003",
                creatorId: "study",
                count: 1,
                customName: null,
                limit: 4,
                access: "public",
                members: ["Drew"],
                owner: "Drew",
                muted: {},
                deafened: {},
                banned: [],
                notes: [],
                mention: false,
                mentionFading: false,
                stamp: "Today at 9:06 PM",
            },
        ];
    }

    function iconFor(access) {
        if (access === "lock") return ICON_LOCK;
        if (access === "hide") return ICON_HIDE;
        return ICON_SPEAKER;
    }

    function parkBubbles() {
        const host = $("creator-bubbles");
        document.querySelectorAll(".creator-bubble").forEach(function (bubble) {
            host.append(bubble);
        });
    }

    function placeCreatorBubbles() {
        const host = $("creator-bubbles");
        const wide = window.matchMedia("(min-width: 768px)").matches;
        if (!wide) {
            CREATORS.forEach(function (creator) {
                const button = document.querySelector('#voice-list button[data-kind="creator"][data-id="' + creator.id + '"]');
                const bubble = document.querySelector('.creator-bubble[data-creator="' + creator.id + '"]');
                if (!button || !bubble) return;
                let slot = button.closest(".creator-slot");
                if (!slot) {
                    slot = el("div", { class: "creator-slot flex items-center gap-1.5" });
                    button.replaceWith(slot);
                    slot.append(button);
                }
                bubble.classList.add("is-inline", "is-placed");
                bubble.classList.remove("is-offscreen");
                bubble.style.top = "";
                bubble.querySelector(".creator-bubble__tail").style.top = "";
                if (bubble.parentElement !== slot) slot.append(bubble);
            });
            return;
        }

        parkBubbles();
        document.querySelectorAll(".creator-slot").forEach(function (slot) {
            const button = slot.querySelector("button");
            if (button) slot.replaceWith(button);
        });

        const hostRect = host.getBoundingClientRect();
        const listRect = $("voice-list").getBoundingClientRect();
        let nextTop = 0;
        CREATORS.forEach(function (creator) {
            const button = document.querySelector('#voice-list button[data-kind="creator"][data-id="' + creator.id + '"]');
            const bubble = document.querySelector('.creator-bubble[data-creator="' + creator.id + '"]');
            if (!button || !bubble) return;
            bubble.classList.remove("is-inline");
            bubble.classList.add("is-placed");
            const bounds = button.getBoundingClientRect();
            const visible = bounds.bottom > listRect.top + 1 && bounds.top < listRect.bottom - 1;
            bubble.classList.toggle("is-offscreen", !visible);
            const height = bubble.offsetHeight;
            const center = bounds.top + bounds.height / 2 - hostRect.top;
            let top = center - height / 2;
            if (top < nextTop) top = nextTop;
            if (top < 0) top = 0;
            bubble.style.top = top + "px";
            const tailTop = Math.max(12, Math.min(Math.max(height - 12, 12), center - top));
            bubble.querySelector(".creator-bubble__tail").style.top = tailTop + "px";
            nextTop = top + height + 8;
        });
    }

    function renderVoice() {
        parkBubbles();
        const list = $("voice-list");
        list.replaceChildren();
        const label = el("p", { class: "px-2 mt-1 mb-1 text-[11px] font-semibold uppercase tracking-wide text-[#949ba4]", text: "Voice Channels" });
        list.append(label);
        CREATORS.forEach(function (creator) {
            const selected = state.view.type === "creator" && state.view.id === creator.id;
            const button = el("button", {
                type: "button",
                class: "chan" + (selected ? " is-selected" : ""),
                "data-kind": "creator",
                "data-id": creator.id,
            });
            const icon = el("span", { class: "shrink-0 flex" });
            icon.innerHTML = ICON_SPEAKER;
            button.append(icon, el("span", { class: "truncate min-w-0", text: creator.name }));
            list.append(button);
            state.rooms.filter(function (room) { return room.creatorId === creator.id; }).forEach(function (room) {
                const roomSelected = state.view.type === "room" && state.view.id === room.id;
                const roomButton = el("button", {
                    type: "button",
                    class: "chan" + (roomSelected ? " is-selected" : ""),
                    "data-kind": "room",
                    "data-id": room.id,
                });
                const roomIcon = el("span", { class: "shrink-0 flex" });
                roomIcon.innerHTML = iconFor(room.access);
                const count = room.members.length;
                roomButton.append(
                    roomIcon,
                    el("span", { class: "truncate min-w-0", text: channelName(room) }),
                    el("span", { class: "ml-auto shrink-0 text-xs tabular-nums", text: room.limit > 0 ? count + "/" + room.limit : String(count) })
                );
                list.append(roomButton);
                const members = el("ul", { class: "mt-0.5 mb-1 space-y-0.5" });
                room.members.forEach(function (name) {
                    const tags = [];
                    if (room.muted[name]) tags.push("Muted");
                    if (room.deafened[name]) tags.push("Deafened");
                    if (room.owner === name) tags.push("Owner");
                    const row = el("li", { class: "flex items-center gap-2 pl-7 pr-2 py-0.5 text-sm text-[#b5bac1]" }, [
                        el("span", {
                            class: "w-5 h-5 rounded-full text-[10px] text-white font-semibold flex items-center justify-center shrink-0",
                            style: "background:" + USERS[name].color,
                            text: name.slice(0, 1),
                            "aria-hidden": "true",
                        }),
                        el("span", {
                            class: (name === state.actor ? "text-white " : "") + "truncate min-w-0",
                            text: name === state.actor ? name + " (you)" : name,
                        }),
                    ]);
                    if (tags.length) {
                        row.append(el("span", {
                            class: "ml-auto text-[10px] text-[#949ba4] shrink-0",
                            text: tags.join(" "),
                        }));
                    }
                    members.append(row);
                });
                list.append(members);
            });
        });
    }

    function inlineCode(text) {
        return el("code", { class: "bg-[#1e1f22] text-[#dbdee1] px-1 rounded font-mono text-[0.85em]", text: text });
    }

    function codePair(name, id) {
        const wrap = el("span");
        wrap.append(inlineCode(name));
        wrap.append(document.createTextNode(" ("));
        wrap.append(inlineCode(id));
        wrap.append(document.createTextNode(")"));
        return wrap;
    }

    function userField(entry, withNameRepeat) {
        const wrap = el("span");
        wrap.append(inlineCode(entry.userName));
        wrap.append(document.createTextNode(" ("));
        if (withNameRepeat) {
            wrap.append(inlineCode(entry.userName));
            wrap.append(document.createTextNode(", "));
        }
        wrap.append(inlineCode(entry.userId));
        wrap.append(document.createTextNode(")"));
        return wrap;
    }

    function embedField(name, valueNode) {
        return el("div", { class: "mt-2" }, [
            el("p", { class: "text-sm font-semibold text-white leading-tight", text: name }),
            el("p", { class: "text-sm text-[#dbdee1] break-words leading-snug" }, [valueNode]),
        ]);
    }

    function logMessage(entry) {
        const styles = {
            channel_create: { title: "TempChannel Create", color: "#2ecc71" },
            channel_remove: { title: "TempChannel Removed", color: "#e67e22" },
            channel_rename: { title: "TempChannel Rename", color: "#fee75c" },
            profanity_block: { title: "TempChannel Blocked Rename", color: "#e74c3c" },
        };
        const style = styles[entry.kind];
        const body = el("div", { class: "min-w-0 flex-1 px-2.5 py-2" }, [
            el("p", { class: "text-sm font-semibold text-white leading-snug", text: style.title }),
        ]);
        if (entry.kind === "channel_create") {
            body.append(embedField("Channel", codePair(entry.channelName, entry.channelId)));
            body.append(embedField("User", userField(entry, false)));
        } else if (entry.kind === "channel_remove") {
            body.append(embedField("Channel", codePair(entry.channelName, entry.channelId)));
            body.append(embedField("Last Connected User", userField(entry, false)));
        } else if (entry.kind === "channel_rename") {
            body.append(embedField("Old Channel", codePair(entry.oldName, entry.channelId)));
            body.append(embedField("User", userField(entry, true)));
            body.append(embedField("New Name", inlineCode(entry.newName)));
        } else {
            body.append(embedField("Channel", codePair(entry.channelName, entry.channelId)));
            body.append(embedField("User", userField(entry, true)));
            body.append(embedField("New Name (Blocked)", inlineCode(entry.newName)));
            body.append(embedField("Flagged for", inlineCode(entry.flagged)));
        }
        const footer = el("p", { class: "text-[11px] text-[#949ba4] mt-2" });
        if (entry.kind === "profanity_block") {
            footer.append(document.createTextNode("Toggle with /settings"));
            footer.append(el("span", { class: "mx-1", "aria-hidden": "true", text: "•" }));
        }
        footer.append(document.createTextNode(entry.stamp));
        body.append(footer);
        const embed = el("div", { class: "mt-1 flex overflow-hidden rounded bg-[#2b2d31] max-w-[432px]" }, [
            el("div", { class: "w-1 shrink-0", style: "background:" + style.color, "aria-hidden": "true" }),
            body,
        ]);
        return el("div", { class: "flex gap-2 px-1" }, [
            el("div", {
                class: "w-8 h-8 rounded-full bg-[#5865f2] text-white text-xs font-semibold flex items-center justify-center shrink-0",
                text: "R",
                "aria-hidden": "true",
            }),
            el("div", { class: "min-w-0 flex-1" }, [
                el("div", { class: "flex items-baseline gap-1.5 flex-wrap" }, [
                    el("span", { class: "text-white text-sm font-medium", text: "Robotnic" }),
                    el("span", { class: "text-[10px] leading-none font-medium bg-[#5865f2] text-white px-1 py-0.5 rounded-sm", text: "BOT" }),
                    el("span", { class: "text-[11px] text-[#949ba4]", text: entry.stamp }),
                ]),
                embed,
            ]),
        ]);
    }

    function renderLog() {
        const list = $("log-list");
        const empty = $("log-empty");
        list.replaceChildren();
        empty.classList.toggle("is-hidden", state.log.length > 0);
        state.log.forEach(function (entry) {
            list.append(logMessage(entry));
        });
        const scroller = $("log-scroll");
        scroller.scrollTop = scroller.scrollHeight;
    }

    function renderNotes(room) {
        const wrap = $("system-notes");
        wrap.replaceChildren();
        room.notes.forEach(function (note) {
            wrap.append(el("p", { class: "text-center text-xs text-[#949ba4] py-1", text: note }));
        });
    }

    function render() {
        if (state.view.type === "room" && !roomById(state.view.id)) state.view = { type: "offline" };
        renderVoice();
        const room = currentRoom();
        const creator = state.view.type === "creator" ? creatorById(state.view.id) : null;
        $("view-offline").classList.toggle("is-hidden", state.view.type !== "offline");
        $("view-creator").classList.toggle("is-hidden", state.view.type !== "creator");
        $("view-room").classList.toggle("is-hidden", state.view.type !== "room");
        $("header-hash").classList.add("is-hidden");

        if (state.view.type === "offline") {
            $("header-title").textContent = "Not connected";
            $("header-topic").textContent = state.actor ? "Acting as " + state.actor : "";
            $("composer").textContent = state.actor ? state.actor + " is not in a voice channel" : "You are not connected";
        } else if (creator) {
            $("header-title").textContent = creator.name;
            $("header-topic").textContent = "Creator channel";
            $("composer").textContent = "Join " + creator.name + " to create a channel";
            $("creator-title").textContent = creator.name;
            const limitLabel = creator.limit === 0 ? "no user limit" : "a limit of " + creator.limit;
            const accessLabel = creator.access === "lock" ? " New rooms start locked for @everyone." : "";
            $("creator-copy").textContent = "Joining creates a channel from " + creator.template + " with " + limitLabel + " and moves you into it." + accessLabel;
        } else if (room) {
            const name = channelName(room);
            $("header-title").textContent = name;
            $("header-topic").textContent = room.access === "lock"
                ? "Locked for the target role"
                : room.access === "hide"
                    ? "Hidden from the target role"
                    : "Voice channel";
            $("composer").textContent = "Message " + name;
            $("panel-title").textContent = name;
            $("panel-owner").textContent = room.owner ? "@" + room.owner : "None, available to claim";
            $("panel-limit").textContent = room.limit === 0 ? "♾️ Unlimited" : String(room.limit);
            $("panel-access").textContent = room.access === "lock"
                ? "🔒 Locked"
                : room.access === "hide"
                    ? "🙈 Hidden"
                    : "🌐 Public";
            $("msg-time").textContent = room.stamp;
            $("mention-name").textContent = "@" + (room.owner || "someone");
            $("owner-mention").classList.toggle("is-hidden", !room.mention);
            $("owner-mention").classList.toggle("is-fading", room.mention && room.mentionFading);
            const claimable = !room.owner && state.actor && room.members.indexOf(state.actor) !== -1;
            $("claim-banner").classList.toggle("is-hidden", !claimable);
            const allowed = canControl(room);
            setVariant($("ctrl-public"), room.access === "public" ? "success" : "primary");
            setVariant($("ctrl-lock"), room.access === "lock" ? "success" : "primary");
            setVariant($("ctrl-hide"), room.access === "hide" ? "success" : "primary");
            $("ctrl-public").setAttribute("aria-pressed", room.access === "public" ? "true" : "false");
            $("ctrl-lock").setAttribute("aria-pressed", room.access === "lock" ? "true" : "false");
            $("ctrl-hide").setAttribute("aria-pressed", room.access === "hide" ? "true" : "false");
            CONTROL_IDS.forEach(function (id) {
                $(id).disabled = !allowed;
            });
            renderNotes(room);
        }

        document.querySelectorAll("[data-actor]").forEach(function (button) {
            const on = button.getAttribute("data-actor") === state.actor;
            setVariant(button, on ? "primary" : "secondary");
            button.setAttribute("aria-pressed", on ? "true" : "false");
        });
        $("leave-voice").disabled = !state.actor || !roomContaining(state.actor);
        $("demo-status").textContent = state.status;
        $("demo-status").classList.toggle("is-hidden", !state.status);
        renderLog();
        placeCreatorBubbles();
    }

    function removeMember(room, name) {
        const label = channelName(room);
        room.members = room.members.filter(function (member) { return member !== name; });
        delete room.muted[name];
        delete room.deafened[name];
        if (room.owner === name) room.owner = null;
        if (!room.members.length) {
            state.rooms = state.rooms.filter(function (item) { return item.id !== room.id; });
            if (state.view.type === "room" && state.view.id === room.id) state.view = { type: "offline" };
            logRemove(room, name, label);
            return "deleted";
        }
        room.notes.push(name + " left the channel.");
        return "stayed";
    }

    function watchMention(roomId) {
        later(function () {
            const live = roomById(roomId);
            if (!live) return;
            live.mentionFading = true;
            render();
        }, 1200);
        later(function () {
            const live = roomById(roomId);
            if (!live) return;
            live.mention = false;
            live.mentionFading = false;
            render();
        }, 1700);
    }

    function joinCreator(creatorId) {
        const creator = creatorById(creatorId);
        if (!state.actor) {
            state.view = { type: "creator", id: creatorId };
            state.status = "You're not connected. Act as a user, then join " + creator.name + ".";
            render();
            return;
        }
        const previous = roomContaining(state.actor);
        if (previous) removeMember(previous, state.actor);
        const existing = state.rooms.filter(function (room) { return room.creatorId === creatorId; });
        const count = existing.length ? Math.max.apply(null, existing.map(function (room) { return room.count; })) + 1 : 1;
        const room = {
            id: "r" + state.nextId,
            discordId: "85349087975361700" + state.nextId,
            creatorId: creatorId,
            count: count,
            customName: null,
            limit: creator.limit,
            access: creator.access,
            members: [state.actor],
            owner: state.actor,
            muted: {},
            deafened: {},
            banned: [],
            notes: [],
            mention: true,
            mentionFading: false,
            stamp: discordStamp(new Date()),
        };
        state.nextId += 1;
        state.rooms.push(room);
        state.view = { type: "room", id: room.id };
        state.status = "";
        logEvent({
            kind: "channel_create",
            channelName: channelName(room),
            channelId: room.discordId,
            userName: state.actor,
            userId: USERS[state.actor].id,
        });
        watchMention(room.id);
        render();
    }

    function openRoom(id) {
        const room = roomById(id);
        if (!room) return;
        state.view = { type: "room", id: id };
        if (!state.actor) {
            state.status = "You're not connected. Act as a user to use this panel.";
            render();
            return;
        }
        if (room.members.indexOf(state.actor) !== -1) {
            state.status = canControl(room) ? "" : (room.owner ? "Only " + room.owner + " can change this channel." : "This channel has no owner. Claim it to use the panel.");
            render();
            return;
        }
        if (room.banned.indexOf(state.actor) !== -1) {
            state.status = state.actor + " is banned from this channel.";
            render();
            return;
        }
        if (room.access === "lock" || room.access === "hide") {
            state.status = state.actor + " can't join. This channel is " + (room.access === "lock" ? "locked" : "hidden") + " for the target role.";
            render();
            return;
        }
        if (room.limit > 0 && room.members.length >= room.limit) {
            state.status = state.actor + " can't join. The user limit is full.";
            render();
            return;
        }
        const previous = roomContaining(state.actor);
        if (previous) removeMember(previous, state.actor);
        const live = roomById(id);
        if (!live) return;
        live.members.push(state.actor);
        live.notes.push(state.actor + " joined the channel.");
        state.view = { type: "room", id: id };
        state.status = canControl(live) ? "" : (live.owner ? "Only " + live.owner + " can change this channel." : "This channel has no owner. Claim it to use the panel.");
        render();
    }

    function actAs(name) {
        state.actor = name;
        const room = roomContaining(name);
        if (room) {
            state.view = { type: "room", id: room.id };
            state.status = room.owner === name ? "" : (room.owner ? "Only " + room.owner + " can change this channel." : "This channel has no owner. Claim it to use the panel.");
        } else {
            state.view = { type: "offline" };
            state.status = name + " is not in a voice channel. Join a creator channel.";
        }
        render();
    }

    function leaveVoice() {
        if (!state.actor) return;
        const room = roomContaining(state.actor);
        if (!room) return;
        const id = room.id;
        const result = removeMember(room, state.actor);
        state.view = { type: "offline" };
        state.status = result === "deleted"
            ? "The channel was deleted because it was empty."
            : state.actor + " left the channel.";
        if (result === "deleted" && state.view.type === "room" && state.view.id === id) state.view = { type: "offline" };
        render();
    }

    function openModal(builder) {
        const card = $("modal-card");
        card.replaceChildren();
        builder(card);
        $("modal").classList.add("is-open");
        document.body.style.overflow = "hidden";
        const input = card.querySelector("input");
        const focus = input || card.querySelector("button");
        if (focus) focus.focus();
    }

    function closeModal() {
        const modal = $("modal");
        if (!modal.classList.contains("is-open")) return;
        modal.classList.remove("is-open");
        document.body.style.overflow = "";
        $("modal-card").replaceChildren();
    }

    function modalTitle(card, title) {
        card.append(el("div", { class: "flex items-start justify-between gap-3 mb-3" }, [
            el("h2", { id: "modal-title", class: "text-white text-lg font-semibold", text: title }),
            el("button", {
                type: "button",
                class: "text-[#b5bac1] text-xl leading-none px-1",
                "aria-label": "Close",
                text: "×",
                onclick: closeModal,
            }),
        ]));
    }

    function dcBtn(label, variant, onClick) {
        return el("button", { type: "button", class: "dc-btn dc-btn--" + variant, text: label, onclick: onClick });
    }

    function showError(message) {
        const slot = $("modal-error");
        if (slot) slot.textContent = message;
    }

    function openRename() {
        const room = currentRoom();
        if (!canControl(room)) return;
        const template = creatorById(room.creatorId).template;
        openModal(function (card) {
            const input = el("input", {
                class: "field-input",
                id: "rename-input",
                maxlength: "100",
                autocomplete: "off",
                placeholder: channelName({ customName: null, creatorId: room.creatorId, owner: room.owner, members: room.members, count: room.count }),
                "aria-label": "Channel name",
            });
            input.value = room.customName || "";
            const error = el("p", { id: "modal-error", class: "mt-2 text-sm text-[#fa777c] min-h-[1.25rem]" });
            const form = el("form", {
                onsubmit: function (event) {
                    event.preventDefault();
                    submitRename(input.value);
                },
            }, [
                el("label", { class: "block text-xs font-semibold uppercase tracking-wide text-[#b5bac1] mb-2", for: "rename-input", text: "Channel name" }),
                input,
                el("p", { class: "mt-2 text-xs text-[#949ba4]", text: "Leave blank to use the template " + template + "." }),
                error,
                el("div", { class: "mt-4 flex justify-end gap-2" }, [
                    dcBtn("Cancel", "secondary", closeModal),
                    dcBtn("Rename", "primary", function () { submitRename(input.value); }),
                ]),
            ]);
            modalTitle(card, "Rename channel");
            card.append(form);
            input.focus();
        });
    }

    function submitRename(raw) {
        const room = currentRoom();
        if (!canControl(room)) return;
        const value = raw.trim();
        if (value.length > 100) {
            showError("Channel names can be at most 100 characters.");
            return;
        }
        if (value.toLowerCase().indexOf("badword") !== -1) {
            logEvent({
                kind: "profanity_block",
                channelName: channelName(room),
                channelId: room.discordId,
                userName: state.actor,
                userId: USERS[state.actor].id,
                newName: value,
                flagged: "badword",
            });
            showError("That name was blocked by the profanity filter.");
            render();
            return;
        }
        const from = channelName(room);
        room.customName = value ? value : null;
        const to = channelName(room);
        if (from !== to) {
            logEvent({
                kind: "channel_rename",
                oldName: from,
                newName: to,
                channelId: room.discordId,
                userName: state.actor,
                userId: USERS[state.actor].id,
            });
        }
        state.status = "";
        closeModal();
        render();
    }

    function openLimit() {
        const room = currentRoom();
        if (!canControl(room)) return;
        openModal(function (card) {
            const input = el("input", {
                class: "field-input",
                id: "limit-input",
                inputmode: "numeric",
                autocomplete: "off",
                "aria-label": "User limit",
            });
            input.value = String(room.limit);
            const error = el("p", { id: "modal-error", class: "mt-2 text-sm text-[#fa777c] min-h-[1.25rem]" });
            function submit() {
                const raw = input.value.trim();
                if (!/^\d+$/.test(raw) || Number(raw) > 99) {
                    showError("Enter a whole number from 0 to 99.");
                    return;
                }
                room.limit = Number(raw);
                state.status = "";
                closeModal();
                render();
            }
            const form = el("form", {
                onsubmit: function (event) {
                    event.preventDefault();
                    submit();
                },
            }, [
                el("label", { class: "block text-xs font-semibold uppercase tracking-wide text-[#b5bac1] mb-2", for: "limit-input", text: "User limit" }),
                input,
                el("p", { class: "mt-2 text-xs text-[#949ba4]", text: "0 is unlimited. Otherwise 1–99." }),
                error,
                el("div", { class: "mt-4 flex justify-end gap-2" }, [
                    dcBtn("Cancel", "secondary", closeModal),
                    dcBtn("Save", "primary", submit),
                ]),
            ]);
            modalTitle(card, "Edit user limit");
            card.append(form);
            input.focus();
            input.select();
        });
    }

    function openBan() {
        const room = currentRoom();
        if (!canControl(room)) return;
        openModal(function (card) {
            modalTitle(card, "Ban / Allow");
            const names = room.members.filter(function (name) { return name !== state.actor; });
            room.banned.forEach(function (name) {
                if (names.indexOf(name) === -1) names.push(name);
            });
            if (!names.length) {
                card.append(el("p", { class: "text-sm text-[#b5bac1]", text: "No one else is in this channel." }));
            }
            names.forEach(function (name) {
                const banned = room.banned.indexOf(name) !== -1;
                card.append(el("div", { class: "flex items-center justify-between gap-3 py-2 border-b border-white/10" }, [
                    el("div", {}, [
                        el("p", { class: "text-white", text: name }),
                        el("p", { class: "text-xs text-[#949ba4]", text: banned ? "Banned" : "In the channel" }),
                    ]),
                    banned
                        ? dcBtn("Allow", "success", function () {
                            room.banned = room.banned.filter(function (item) { return item !== name; });
                            room.notes.push(name + " is allowed in this channel again.");
                            state.status = "";
                            closeModal();
                            render();
                        })
                        : dcBtn("Ban", "danger", function () {
                            room.members = room.members.filter(function (item) { return item !== name; });
                            delete room.muted[name];
                            delete room.deafened[name];
                            if (room.banned.indexOf(name) === -1) room.banned.push(name);
                            if (room.owner === name) room.owner = null;
                            room.notes.push(name + " was banned and disconnected.");
                            state.status = "";
                            if (!room.members.length) {
                                const label = channelName(room);
                                state.rooms = state.rooms.filter(function (item) { return item.id !== room.id; });
                                state.view = { type: "offline" };
                                logRemove(room, name, label);
                            }
                            closeModal();
                            render();
                        }),
                ]));
            });
            card.append(el("div", { class: "mt-4 flex justify-end" }, [dcBtn("Close", "secondary", closeModal)]));
        });
    }

    function openMemberAction(kind) {
        const room = currentRoom();
        if (!canControl(room)) return;
        const label = kind === "mute" ? "Mute" : "Deafen";
        openModal(function (card) {
            modalTitle(card, label + " / " + (kind === "mute" ? "Unmute" : "Undeafen"));
            const others = room.members.filter(function (name) { return name !== state.actor; });
            if (!others.length) {
                card.append(el("p", { class: "text-sm text-[#b5bac1]", text: "No one else is in this channel." }));
                card.append(el("div", { class: "mt-4 flex justify-end" }, [dcBtn("Close", "secondary", closeModal)]));
                return;
            }
            others.forEach(function (name) {
                const active = kind === "mute" ? Boolean(room.muted[name]) : Boolean(room.deafened[name]);
                card.append(el("div", { class: "flex items-center justify-between gap-3 py-2" }, [
                    el("span", { class: "text-white", text: name }),
                    dcBtn(active ? (kind === "mute" ? "Unmute" : "Undeafen") : label, "secondary", function () {
                        if (kind === "mute") room.muted[name] = !room.muted[name];
                        else room.deafened[name] = !room.deafened[name];
                        state.status = "";
                        closeModal();
                        render();
                    }),
                ]));
            });
        });
    }

    function openGive() {
        const room = currentRoom();
        if (!canControl(room)) return;
        openModal(function (card) {
            modalTitle(card, "Give ownership");
            const targets = room.members.filter(function (name) { return name !== room.owner; });
            if (!targets.length) card.append(el("p", { class: "text-sm text-[#b5bac1]", text: "No one else is in this channel." }));
            targets.forEach(function (name) {
                card.append(el("div", { class: "flex items-center justify-between gap-3 py-2 border-b border-white/10" }, [
                    el("span", { class: "text-white", text: name }),
                    dcBtn("Give", "success", function () {
                        room.owner = name;
                        room.notes.push("Ownership given to " + name + ".");
                        state.status = "Only " + name + " can change this channel.";
                        closeModal();
                        render();
                    }),
                ]));
            });
            const actions = el("div", { class: "mt-4 flex flex-wrap justify-end gap-2" });
            if (room.owner) {
                actions.append(dcBtn("Release ownership", "secondary", function () {
                    room.owner = null;
                    room.notes.push("Ownership released. Anyone in the channel can claim it.");
                    state.status = "This channel has no owner. Claim it to use the panel.";
                    closeModal();
                    render();
                }));
            }
            actions.append(dcBtn("Close", "secondary", closeModal));
            card.append(actions);
        });
    }

    function claim() {
        const room = currentRoom();
        if (!room || room.owner || !state.actor || room.members.indexOf(state.actor) === -1) return;
        room.owner = state.actor;
        room.notes.push(state.actor + " claimed the channel.");
        state.status = "";
        closeModal();
        render();
    }

    function openDelete() {
        const room = currentRoom();
        if (!canControl(room)) return;
        const name = channelName(room);
        openModal(function (card) {
            modalTitle(card, "Delete channel");
            card.append(el("p", { class: "text-sm text-[#dbdee1]", text: "Delete " + name + "? Everyone in it will be disconnected." }));
            card.append(el("div", { class: "mt-4 flex justify-end gap-2" }, [
                dcBtn("Cancel", "secondary", closeModal),
                dcBtn("Delete", "danger", function () {
                    logRemove(room, state.actor, name);
                    state.rooms = state.rooms.filter(function (item) { return item.id !== room.id; });
                    state.view = { type: "offline" };
                    state.status = "";
                    closeModal();
                    render();
                }),
            ]));
        });
    }

    function setAccess(access) {
        const room = currentRoom();
        if (!canControl(room)) return;
        room.access = access;
        state.status = "";
        render();
    }

    function resetDemo() {
        closeModal();
        seed();
        render();
    }

    function bindMain() {
        $("voice-list").addEventListener("click", function (event) {
            const button = event.target.closest("[data-kind]");
            if (!button) return;
            const kind = button.getAttribute("data-kind");
            const id = button.getAttribute("data-id");
            if (kind === "creator") {
                state.view = { type: "creator", id: id };
                state.status = "";
                render();
            } else {
                openRoom(id);
            }
        });
        $("creator-join").addEventListener("click", function () {
            if (state.view.type === "creator") joinCreator(state.view.id);
        });
        document.querySelectorAll("[data-actor]").forEach(function (button) {
            button.addEventListener("click", function () {
                actAs(button.getAttribute("data-actor"));
            });
        });
        $("leave-voice").addEventListener("click", leaveVoice);
        $("reset-demo").addEventListener("click", resetDemo);
        $("ctrl-rename").addEventListener("click", openRename);
        $("ctrl-limit").addEventListener("click", openLimit);
        $("ctrl-give").addEventListener("click", openGive);
        $("ctrl-mute").addEventListener("click", function () { openMemberAction("mute"); });
        $("ctrl-deafen").addEventListener("click", function () { openMemberAction("deafen"); });
        $("ctrl-ban").addEventListener("click", openBan);
        $("ctrl-clear").addEventListener("click", function () {
            const room = currentRoom();
            if (!canControl(room)) return;
            room.notes = [];
            room.mention = false;
            room.mentionFading = false;
            state.status = "";
            render();
        });
        $("ctrl-delete").addEventListener("click", openDelete);
        $("ctrl-public").addEventListener("click", function () { setAccess("public"); });
        $("ctrl-lock").addEventListener("click", function () { setAccess("lock"); });
        $("ctrl-hide").addEventListener("click", function () { setAccess("hide"); });
        $("ctrl-claim").addEventListener("click", claim);
        $("modal").addEventListener("click", function (event) {
            if (event.target.id === "modal") closeModal();
        });
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") closeModal();
        });
    }

    function initHubs() {
        const hubs = {
            gaming: {
                template: "{activity} Lobby",
                name: "Valorant Lobby",
                detail: "TestUser is playing Valorant, so {activity} becomes Valorant. With no game, this hub would create General Lobby.",
            },
            study: {
                template: "Study with {user}",
                name: "Study with TestUser",
                detail: "{user} is the channel owner. The next person to join Study gets their own room.",
            },
            hangout: {
                template: "Hangout #{count}",
                name: "Hangout #1",
                detail: "{count} numbers rooms from this hub so names stay unique.",
            },
        };
        document.querySelectorAll("[data-hub]").forEach(function (button) {
            button.addEventListener("click", function () {
                const hub = hubs[button.getAttribute("data-hub")];
                document.querySelectorAll("[data-hub]").forEach(function (other) {
                    other.classList.toggle("is-selected", other === button);
                });
                $("hub-placeholder").classList.add("is-hidden");
                $("hub-created").classList.remove("is-hidden");
                $("hub-template").textContent = "Template  " + hub.template;
                $("hub-name").textContent = hub.name;
                $("hub-moved").textContent = "TestUser moved into the new channel. " + button.textContent.trim() + " stays open for the next person.";
                $("hub-detail").textContent = hub.detail;
            });
        });
    }

    function init() {
        seed();
        bindMain();
        initHubs();
        render();
        $("voice-list").addEventListener("scroll", placeCreatorBubbles);
        window.addEventListener("resize", placeCreatorBubbles);
    }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
})();

#include <algorithm>
#include <fstream>
#include <iostream>
#include <regex>
#include <set>
#include <sstream>
#include <string>
#include <vector>

struct Subject {
    std::vector<int> teachers;
    int lectures;
    bool is_lab;
};

struct Assignment {
    int batch;
    int subject;
    int teacher;
    int room;
    int slot;
};

struct Task {
    int batch;
    int subject;
    int duration;
};

struct InputData {
    std::vector<Subject> subjects;
    int rooms = 0;
    int slots = 0;
    int batches = 0;
    int teachers = 0;
    std::vector<std::vector<int>> batch_subjects;
    std::set<int> lunch_slots;
};

std::string read_file(const std::string& path) {
    std::ifstream input(path);
    if (!input.is_open()) {
        throw std::runtime_error("Failed to open " + path);
    }
    std::ostringstream buffer;
    buffer << input.rdbuf();
    return buffer.str();
}

std::string extract_array_block(const std::string& text, const std::string& key) {
    const std::string needle = "\"" + key + "\"";
    std::size_t key_pos = text.find(needle);
    if (key_pos == std::string::npos) {
        return "";
    }

    std::size_t open_pos = text.find('[', key_pos);
    if (open_pos == std::string::npos) {
        return "";
    }

    int depth = 0;
    for (std::size_t index = open_pos; index < text.size(); ++index) {
        if (text[index] == '[') {
            ++depth;
        } else if (text[index] == ']') {
            --depth;
            if (depth == 0) {
                return text.substr(open_pos + 1, index - open_pos - 1);
            }
        }
    }

    return "";
}

std::vector<int> extract_int_array(const std::string& text, const std::string& key) {
    std::vector<int> values;
    const std::string block = extract_array_block(text, key);
    std::regex number_regex("-?\\d+");

    auto begin = std::sregex_iterator(block.begin(), block.end(), number_regex);
    auto end = std::sregex_iterator();
    for (auto it = begin; it != end; ++it) {
        values.push_back(std::stoi((*it).str()));
    }

    return values;
}

std::vector<std::vector<int>> extract_nested_int_arrays(const std::string& text, const std::string& key) {
    std::vector<std::vector<int>> groups;
    const std::string block = extract_array_block(text, key);
    int depth = 0;
    std::size_t start = std::string::npos;

    for (std::size_t index = 0; index < block.size(); ++index) {
        if (block[index] == '[') {
            if (depth == 0) {
                start = index;
            }
            ++depth;
        } else if (block[index] == ']') {
            --depth;
            if (depth == 0 && start != std::string::npos) {
                const std::string item = block.substr(start + 1, index - start - 1);
                std::vector<int> values;
                std::regex number_regex("-?\\d+");
                auto begin = std::sregex_iterator(item.begin(), item.end(), number_regex);
                auto end = std::sregex_iterator();
                for (auto it = begin; it != end; ++it) {
                    values.push_back(std::stoi((*it).str()));
                }
                groups.push_back(values);
                start = std::string::npos;
            }
        }
    }

    return groups;
}

int extract_int_value(const std::string& text, const std::string& key) {
    std::regex pattern("\"" + key + "\"\\s*:\\s*(\\d+)");
    std::smatch match;
    if (!std::regex_search(text, match, pattern)) {
        throw std::runtime_error("Missing integer field: " + key);
    }
    return std::stoi(match[1].str());
}

bool extract_bool_value(const std::string& text, const std::string& key) {
    std::regex pattern("\"" + key + "\"\\s*:\\s*(true|false)");
    std::smatch match;
    if (!std::regex_search(text, match, pattern)) {
        throw std::runtime_error("Missing boolean field: " + key);
    }
    return match[1].str() == "true";
}

std::vector<std::string> extract_subject_objects(const std::string& text) {
    std::vector<std::string> objects;
    const std::string subjects_block = extract_array_block(text, "subjects");
    int depth = 0;
    std::size_t start = std::string::npos;

    for (std::size_t index = 0; index < subjects_block.size(); ++index) {
        if (subjects_block[index] == '{') {
            if (depth == 0) {
                start = index;
            }
            ++depth;
        } else if (subjects_block[index] == '}') {
            --depth;
            if (depth == 0 && start != std::string::npos) {
                objects.push_back(subjects_block.substr(start, index - start + 1));
                start = std::string::npos;
            }
        }
    }

    return objects;
}

InputData parse_input(const std::string& text) {
    InputData data;
    data.rooms = extract_int_value(text, "rooms");
    data.slots = extract_int_value(text, "slots");
    data.batches = extract_int_value(text, "batches");
    data.teachers = extract_int_value(text, "teachers");
    data.batch_subjects = extract_nested_int_arrays(text, "batch_subjects");

    for (int lunch_slot : extract_int_array(text, "lunch_slots")) {
        data.lunch_slots.insert(lunch_slot);
    }

    for (const std::string& raw_subject : extract_subject_objects(text)) {
        Subject subject;
        subject.teachers = extract_int_array(raw_subject, "teachers");
        subject.lectures = extract_int_value(raw_subject, "lectures");
        subject.is_lab = extract_bool_value(raw_subject, "is_lab");
        data.subjects.push_back(subject);
    }

    return data;
}

class Scheduler {
public:
    explicit Scheduler(const InputData& input)
        : subjects(input.subjects),
          num_rooms(input.rooms),
          num_slots(input.slots),
          num_batches(input.batches),
          num_teachers(input.teachers),
          batch_subjects(input.batch_subjects),
          lunch_slots(input.lunch_slots),
          teacher_busy(num_teachers, std::vector<bool>(num_slots, false)),
          room_busy(num_rooms, std::vector<bool>(num_slots, false)),
          batch_busy(num_batches, std::vector<bool>(num_slots, false)) {}

    bool solve() {
        tasks.clear();

        if (static_cast<int>(batch_subjects.size()) != num_batches) {
            return false;
        }

        for (int batch = 0; batch < num_batches; ++batch) {
            for (int subject_index : batch_subjects[batch]) {
                if (subject_index < 0 || subject_index >= static_cast<int>(subjects.size())) {
                    return false;
                }

                const Subject& subject = subjects[subject_index];
                if (subject.is_lab) {
                    if (subject.lectures % 2 != 0) {
                        return false;
                    }
                    for (int count = 0; count < subject.lectures / 2; ++count) {
                        tasks.push_back({batch, subject_index, 2});
                    }
                } else {
                    for (int count = 0; count < subject.lectures; ++count) {
                        tasks.push_back({batch, subject_index, 1});
                    }
                }
            }
        }

        std::sort(tasks.begin(), tasks.end(), [&](const Task& left, const Task& right) {
            const Subject& left_subject = subjects[left.subject];
            const Subject& right_subject = subjects[right.subject];
            if (left.duration != right.duration) {
                return left.duration > right.duration;
            }
            if (left_subject.teachers.size() != right_subject.teachers.size()) {
                return left_subject.teachers.size() < right_subject.teachers.size();
            }
            return left.subject < right.subject;
        });

        return greedy_assign();
    }

    std::string to_json() const {
        std::ostringstream output;
        output << "{\n  \"timetable\": [\n";
        for (std::size_t index = 0; index < timetable.size(); ++index) {
            const Assignment& assignment = timetable[index];
            output << "    {\"batch\": " << assignment.batch
                   << ", \"subject\": " << assignment.subject
                   << ", \"teacher\": " << assignment.teacher
                   << ", \"room\": " << assignment.room
                   << ", \"slot\": " << assignment.slot << "}";
            if (index + 1 != timetable.size()) {
                output << ",";
            }
            output << "\n";
        }
        output << "  ]\n}\n";
        return output.str();
    }

private:
    std::vector<Subject> subjects;
    int num_rooms;
    int num_slots;
    int num_batches;
    int num_teachers;
    std::vector<std::vector<int>> batch_subjects;
    std::set<int> lunch_slots;
    std::vector<std::vector<bool>> teacher_busy;
    std::vector<std::vector<bool>> room_busy;
    std::vector<std::vector<bool>> batch_busy;
    std::vector<Task> tasks;
    std::vector<Assignment> timetable;

    bool is_slot_range_free(int batch, int teacher, int room, int start_slot, int duration) const {
        for (int offset = 0; offset < duration; ++offset) {
            int slot = start_slot + offset;
            if (slot >= num_slots || lunch_slots.count(slot) > 0) {
                return false;
            }
            if (batch_busy[batch][slot] || teacher_busy[teacher][slot] || room_busy[room][slot]) {
                return false;
            }
        }
        return true;
    }

    void assign_range(int batch, int teacher, int room, int subject, int start_slot, int duration, bool state) {
        for (int offset = 0; offset < duration; ++offset) {
            int slot = start_slot + offset;
            batch_busy[batch][slot] = state;
            teacher_busy[teacher][slot] = state;
            room_busy[room][slot] = state;
            if (state) {
                timetable.push_back({batch, subject, teacher, room, slot});
            } else {
                timetable.pop_back();
            }
        }
    }

    bool greedy_assign() {
        std::vector<int> room_load(num_rooms, 0);
        std::vector<int> teacher_load(num_teachers, 0);

        for (const Task& task : tasks) {
            const Subject& subject = subjects[task.subject];

            bool assigned = false;
            int best_teacher = -1;
            int best_room = -1;
            int best_slot = -1;
            int best_score = 1'000'000'000;

            for (int teacher : subject.teachers) {
                if (teacher < 0 || teacher >= num_teachers) {
                    continue;
                }
                for (int room = 0; room < num_rooms; ++room) {
                    for (int slot = 0; slot < num_slots; ++slot) {
                        if (!is_slot_range_free(task.batch, teacher, room, slot, task.duration)) {
                            continue;
                        }

                        const int score =
                            slot * 100 +
                            teacher_load[teacher] * 10 +
                            room_load[room];

                        if (score < best_score) {
                            best_score = score;
                            best_teacher = teacher;
                            best_room = room;
                            best_slot = slot;
                            assigned = true;
                        }
                    }
                }
            }

            if (!assigned) {
                return false;
            }

            assign_range(task.batch, best_teacher, best_room, task.subject, best_slot, task.duration, true);
            teacher_load[best_teacher] += task.duration;
            room_load[best_room] += task.duration;
        }

        return true;
    }
};

int main() {
    try {
        const std::string raw_input = read_file("../data/input.json");
        const InputData input = parse_input(raw_input);
        Scheduler scheduler(input);

        std::ofstream output("../data/output.json");
        if (!output.is_open()) {
            std::cerr << "Failed to open ../data/output.json" << std::endl;
            return 1;
        }

        if (!scheduler.solve()) {
            output << "{\n  \"timetable\": []\n}\n";
            return 1;
        }

        output << scheduler.to_json();
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << std::endl;
        return 1;
    }
}

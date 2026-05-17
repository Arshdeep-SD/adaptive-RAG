import { useState } from "react";

interface FormField {
  name: string;
  label: string;
  type: "text" | "number" | "select";
  options?: string[];
}

interface FormProps {
  fields?: FormField[];
  submit_action?: string;
}

export function FormComponent({ fields = [], submit_action = "Submit" }: FormProps) {
  const [values, setValues] = useState<Record<string, string>>({});

  const handleChange = (name: string, value: string) => {
    setValues((v) => ({ ...v, [name]: value }));
  };

  return (
    <form
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        console.info("Form submit:", values);
      }}
    >
      {fields.map((field) => (
        <div key={field.name} className="flex flex-col gap-1">
          <label className="text-sm font-medium text-gray-700">{field.label}</label>
          {field.type === "select" ? (
            <select
              className="border border-gray-300 rounded px-3 py-1.5 text-sm"
              value={values[field.name] ?? ""}
              onChange={(e) => handleChange(field.name, e.target.value)}
            >
              <option value="">Select...</option>
              {(field.options ?? []).map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          ) : (
            <input
              type={field.type}
              className="border border-gray-300 rounded px-3 py-1.5 text-sm"
              value={values[field.name] ?? ""}
              onChange={(e) => handleChange(field.name, e.target.value)}
            />
          )}
        </div>
      ))}
      <button
        type="submit"
        className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded hover:bg-indigo-700"
      >
        {submit_action}
      </button>
    </form>
  );
}

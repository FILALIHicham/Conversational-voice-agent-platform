import { useEffect, useState } from 'react';
import { IconX } from '@tabler/icons-react';

interface Field {
  name: string;
  label: string;
  type: 'text' | 'email' | 'number' | 'select' | 'date';
  options?: { value: string; label: string }[];
}

interface EditModalProps<T> {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: T) => void;
  data: T;
  fields: Field[];
  title: string;
}

const EditModal = <T extends Record<string, any>>({
  isOpen,
  onClose,
  onSave,
  data,
  fields,
  title
}: EditModalProps<T>) => {
  const [formData, setFormData] = useState<T>(data);

  useEffect(() => {
    setFormData(data);
  }, [data]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    let processedValue: any = value;
    if (type === 'number') {
      processedValue = parseFloat(value);
    }
    
    setFormData(prev => ({
      ...prev,
      [name]: processedValue
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-dark-900/80 backdrop-blur-sm" onClick={onClose}></div>
      
      <div className="relative z-10 w-full max-w-md transform rounded-xl bg-dark-800 border border-dark-700/50 p-6 shadow-xl transition-all">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-white">{title}</h3>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-dark-400 hover:text-white hover:bg-dark-700"
          >
            <IconX size={18} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {fields.map((field) => (
            <div key={field.name}>
              <label htmlFor={field.name} className="block text-sm font-medium text-dark-300 mb-1">
                {field.label}
              </label>
              
              {field.type === 'select' ? (
                <select
                  id={field.name}
                  name={field.name}
                  value={String(formData[field.name])}
                  onChange={handleChange}
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg py-2 px-3 text-white focus:outline-none focus:ring-1 focus:ring-primary-500"
                >
                  {field.options?.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={field.type}
                  id={field.name}
                  name={field.name}
                  value={formData[field.name] !== undefined ? String(formData[field.name]) : ''}
                  onChange={handleChange}
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg py-2 px-3 text-white focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              )}
            </div>
          ))}
          
          <div className="flex justify-end space-x-3 pt-3">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-outline bg-transparent text-white border-dark-600 hover:bg-dark-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn bg-primary-500 text-white hover:bg-primary-600"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditModal;
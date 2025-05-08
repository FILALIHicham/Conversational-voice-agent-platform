import { useState } from 'react';
import { IconDotsVertical, IconEdit, IconTrash } from '@tabler/icons-react';

export interface DataTableColumn<T> {
  header: string;
  accessor: keyof T;
  render?: (value: any, row: T) => React.ReactNode;
}

interface DataTableProps<T> {
  data: T[];
  columns: DataTableColumn<T>[];
  onEdit?: (row: T) => void;
  onDelete?: (row: T) => void;
  idField?: keyof T;
}

const DataTable = <T extends object>({ 
  data, 
  columns, 
  onEdit, 
  onDelete, 
  idField = 'id' as keyof T
}: DataTableProps<T>) => {
  const [activeMenu, setActiveMenu] = useState<any>(null);

  const toggleMenu = (id: any) => {
    if (activeMenu === id) {
      setActiveMenu(null);
    } else {
      setActiveMenu(id);
    }
  };

  return (
    <div className="overflow-x-auto rounded-xl shadow-md bg-dark-800/50 backdrop-blur-sm border border-dark-700/50">
      <table className="min-w-full divide-y divide-dark-700/50">
        <thead>
          <tr className="bg-dark-900/50">
            {columns.map((column, idx) => (
              <th 
                key={idx} 
                className="px-6 py-4 text-left text-xs font-medium text-dark-400 uppercase tracking-wider"
              >
                {column.header}
              </th>
            ))}
            <th className="px-6 py-4 text-right text-xs font-medium text-dark-400 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-dark-700/50">
          {data.map((row, rowIdx) => (
            <tr 
              key={String(row[idField]) || rowIdx}
              className="hover:bg-dark-800/80 transition-colors"
            >
              {columns.map((column, colIdx) => (
                <td key={colIdx} className="px-6 py-4 whitespace-nowrap text-sm text-white">
                  {column.render ? column.render(row[column.accessor], row) : String(row[column.accessor] || '')}
                </td>
              ))}
              <td className="px-6 py-4 whitespace-nowrap text-sm text-white text-right relative">
                <button 
                  onClick={() => toggleMenu(row[idField])}
                  className="p-2 rounded-full hover:bg-dark-700 transition-colors"
                >
                  <IconDotsVertical size={16} />
                </button>
                
                {activeMenu === row[idField] && (
                  <div className="absolute right-0 mt-2 w-48 bg-dark-800 border border-dark-700 rounded-md shadow-lg z-50 overflow-hidden">
                    <div className="py-1">
                      {onEdit && (
                        <button
                          onClick={() => {
                            onEdit(row);
                            setActiveMenu(null);
                          }}
                          className="w-full px-4 py-2 text-left text-sm text-white hover:bg-dark-700 flex items-center gap-2"
                        >
                          <IconEdit size={16} />
                          Edit
                        </button>
                      )}
                      
                      {onDelete && (
                        <button
                          onClick={() => {
                            onDelete(row);
                            setActiveMenu(null);
                          }}
                          className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-dark-700 flex items-center gap-2"
                        >
                          <IconTrash size={16} />
                          Delete
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataTable;